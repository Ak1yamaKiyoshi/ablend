class PID:
    def __init__(self, k_p, k_i, k_d) -> None:
        self.k_p = k_p
        self.k_i = k_i
        self.k_d = k_d
        self.previous_error = 0.0
        self.integral = 0.0

    def reset(self):
        self.previous_error = 0.0
        self.integral = 0.0

    def control(self, current_error, dt):
        self.integral += current_error * dt
        prop_term = self.k_p * current_error
        int_term = self.k_i * self.integral
        der_term = self.k_d * (current_error - self.previous_error) / dt
        self.previous_error = current_error

        return prop_term + int_term + der_term
