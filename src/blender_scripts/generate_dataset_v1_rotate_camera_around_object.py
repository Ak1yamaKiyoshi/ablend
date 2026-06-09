import bpy 
from mathutils import Vector, Euler
import time
import math
import random
import queue
import os
scene = bpy.context.scene

""" 
This script used for generating synthetic dataset while rotating camera around Target object in blender. 


blender data/camera-movement-test.blend --python blender_scripts/blender_scripts/generate_dataset_v1_rotate_camera_around_object.py 
blender data/car-scene.blend --python blender_scripts/blender_scripts/generate_dataset_v1_rotate_camera_around_object.py
""" 


def move_camera_by_elevation_rotation_and_distance_and_point_to_target_with_offset(cam, target, elevation, rotation, distance, camera_object_offset_x, camera_object_offset_y):
  x, y, z = [0.0, distance, 0.0]
  pitch_rad = math.radians(elevation)
  yaw_rad = math.radians(rotation)

  # set camera position from distance, elevation and rotation 
  # https://www.cs.helsinki.fi/group/goa/mallinnus/3dtransf/3drot.html
  y_new = y * math.cos(pitch_rad) - z * math.sin(pitch_rad)
  z_new = y * math.sin(pitch_rad) + z * math.cos(pitch_rad)
  x_new = x # rotation around x axis (pitch..?)

  x = x_new
  y = y_new
  z = z_new
  
  x_new = x * math.cos(yaw_rad) - y * math.sin(yaw_rad)
  y_new = x * math.sin(yaw_rad) + y * math.cos(yaw_rad)
  z_new = z # rotation around z axis (yaw ..?)

  x = x_new
  y = y_new
  z = z_new

  cam.location = target.location.copy() + Vector([x, y, z])

  # point camera to target 
  direction = target.location - cam.location
  cam.rotation_mode = 'XYZ'  
  base_rot = direction.to_track_quat('-Z', 'Y')
  
  # add offset where amera is pointing 
  offset_rot = Euler((cam.data.angle_y * camera_object_offset_y, cam.data.angle_x * camera_object_offset_x, 0.0), 'XYZ').to_quaternion()
  cam.rotation_euler = (base_rot @ offset_rot).to_euler('XYZ')


def setup_flat_color_mask(target_obj, mask_color=(1.0, 0.0, 1.0, 1.0)):
    #aigenerated, todo: refactor, test with other materials
    mask_mat = bpy.data.materials.new(name="Mask_Material")
    mask_mat.use_nodes = True
    nodes = mask_mat.node_tree.nodes
    nodes.clear()
    
    shader_emission = nodes.new(type='ShaderNodeEmission')
    shader_emission.inputs['Color'].default_value = mask_color
    
    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    mask_mat.node_tree.links.new(shader_emission.outputs['Emission'], node_output.inputs['Surface'])
    
    target_obj["orig_materials"] = [slot.material for slot in target_obj.material_slots]

    if not target_obj.material_slots:
        target_obj.data.materials.append(mask_mat)
    else:
        for slot in target_obj.material_slots:
            slot.material = mask_mat

def reset_flat_color_mask(target_obj):
    #aigenerated todo: refactor, test with other materials
    if "orig_materials" in target_obj:
        orig_mats = target_obj["orig_materials"]
        for i, mat in enumerate(orig_mats):
            if i < len(target_obj.material_slots):
                target_obj.material_slots[i].material = mat
        del target_obj["orig_materials"]
        
    mask_mat = bpy.data.materials.get("Mask_Material")
    if mask_mat:
        bpy.data.materials.remove(mask_mat)


def main():

  global sample_queue
  sample = sample_queue.get_nowait()
  cam = bpy.data.objects.get("Camera")
  target = bpy.data.objects.get("Target")
  render_width, render_height = sample['resolution']

  area = [a for a in bpy.context.screen.areas if a.type == 'VIEW_3D'][0]
  space = area.spaces.active
  space.shading.type = 'RENDERED'
  bpy.context.scene.render.engine = 'BLENDER_EEVEE'
  space.region_3d.view_perspective = 'CAMERA'

  # renderer settings
  scene = bpy.context.scene
  #scene.render.preview_pixel_size = '8'
  cam.data.show_passepartout = True
  cam.data.passepartout_alpha = 1.0
  region = next(r for r in area.regions if r.type == 'WINDOW')
  with bpy.context.temp_override(area=area, region=region):
      bpy.ops.view3d.view_center_camera()

  #set camera resolution and fov 
  scene.render.resolution_x = render_width
  scene.render.resolution_y = render_height
  aspect_ratio = render_width / render_height

  diag_fov_rad = math.radians(sample['fov'])
  horizontal_fov_rad = 2 * math.atan(
      math.tan(diag_fov_rad / 2.0) / math.sqrt(1.0 + (1.0 / (aspect_ratio ** 2)))
  )
  cam.data.lens_unit = "FOV"
  cam.data.angle_x = horizontal_fov_rad

  # move camera 
  move_camera_by_elevation_rotation_and_distance_and_point_to_target_with_offset(
    cam, target, sample['elevation'],  sample['rotation'], sample['distance'], sample['offset_x'], sample['offset_y']
  )
  
  
  # render image 
  file_dir = "output"
  res_x, res_y = sample['resolution']

  file_base_name = (
      f"{sample['sample_id']:07d}_"
      f"el={sample['elevation']:.2f}_"
      f"rot={sample['rotation']:.2f}_"
      f"dist={sample['distance']:.2f}_"
      f"offx={sample['offset_x']:.3f}_"
      f"offy={sample['offset_y']:.3f}_"
      f"fov={sample['fov']:.1f}_"
      f"res={res_x}x{res_y}"
  )
  render_filepath = os.path.join(file_dir, file_base_name + "_render")
  segmentation_filepath = os.path.join(file_dir, file_base_name + "_segmentation")
  scene.render.image_settings.file_format = 'PNG'
  
  scene.render.filepath = render_filepath
  bpy.ops.render.render(write_still=True)
  
  setup_flat_color_mask(target)
  scene.render.filepath = segmentation_filepath
  bpy.ops.render.render(write_still=True)
  reset_flat_color_mask(target)

  print(f"[sample {sample['sample_id']:06d}]: elevation={sample['elevation']} rotation={sample['rotation']}, distance={sample['distance']}, fov: {sample['fov']} offset_x: {sample['offset_x']} offset_y: {sample['offset_y']} resolution: {sample['resolution']}")
  return 1/100000000


if __name__ == "__main__":
  elevations = [i for i in range(10, 91, 10)]
  rotations = [i for i in range(0, 180, 15)]
  distances = [i for i in range(30, 150, 5)]
  offsets_x = [0.0] # offsets from camera center
  offsets_y = [0.0] # offsets from camera center 
  fovs = [19, 60, 90] # diagonal fov
  resolutions = [[640, 640]] 

  print(f"Samples to generate: {len(elevations) * len(rotations) * len(distances) * len(offsets_x) * len(offsets_y)}")
  
  sample_queue = queue.Queue()

  i = 1
  for el in elevations:
    for d in distances:
      for rot in rotations:
        for offx in offsets_x:
          for offy in offsets_y:
            for f in fovs:
              for res in resolutions:
                sample_queue.put({
                  "elevation": el, 
                  "rotation": rot, 
                  "distance": d, 
                  "offset_x": offx, 
                  "offset_y": offy, 
                  "fov": f, 
                  "sample_id": i,
                  "resolution": res
                })
                i += 1

  print(f"total samples to generate: {i}")


bpy.app.timers.register(main)

