def get_absolute_path(relative_path):
    import os
    return os.path.join(os.path.dirname(__file__), relative_path)
