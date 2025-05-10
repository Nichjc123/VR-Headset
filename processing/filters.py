# processing/filters.py
class LowPassFilter:
    def __init__(self, alpha=0.2):
        self.alpha = alpha
        self.value = None
        
    def update(self, new_value):
        if self.value is None:
            self.value = new_value
        else:
            self.value = self.alpha * new_value + (1 - self.alpha) * self.value
        return self.value