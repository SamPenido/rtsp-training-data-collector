# Configuration constants for the Frame Classifier

# Main categories with simplified naming
CATEGORIES = {
    '0': 'null',
    '1': 'forno_enchendo',
    '2': 'sinterizacao_acontecendo',
    '3': 'despejo_acontecendo',
    '4': 'panela_voltando_posicao_normal',
    '5': 'forno_vazio'
}

# Subcategories for event phases
SUBCATEGORIES = {
    'i': 'inicio',
    'm': 'meio',
    'f': 'fim'
}

# Define colors for better visibility in the UI overlay
COLORS = {
    'bg': (20, 20, 20),           # Dark background
    'header': (50, 200, 255),     # Blue headers
    'text': (255, 255, 255),      # White text
    'highlight': (0, 255, 255),   # Cyan/Yellow for highlights
    'success': (50, 255, 50),     # Green for success/classification
    'warning': (255, 50, 50),     # Red for warnings
    'info': (180, 180, 180),      # Light gray for info text
    'subcategory': (255, 127, 0)  # Orange for selected subcategory
}

# Default JSON filename for storing classifications
DEFAULT_CLASSIFICATION_FILE = "classifications.json"

# Default window dimensions
DEFAULT_WINDOW_WIDTH = 1280
DEFAULT_WINDOW_HEIGHT = 720
