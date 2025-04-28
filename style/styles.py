from ttkbootstrap import Style

def configure_styles(style: Style):
    """Configure global styles"""
    # Base colors
    colors = {
        'bg': 'white',          # White background for most elements
        'sidebar': '#E6E6FA',   # Light purple only for sidebar
        'accent': '#9370DB',    # Medium purple for accents
        'text': '#2C0147',      # Dark purple for text
        'hover': '#F0E6FF'      # Very light purple for hover effects
    }

    # Configure base styles
    style.configure('TFrame', background=colors['bg'])
    style.configure('Content.TFrame', background=colors['bg'])
    style.configure('Sidebar.TFrame', background=colors['sidebar'])
    
    # Configure button styles
    style.configure('Sidebar.TButton',
        background=colors['sidebar'],
        foreground=colors['text'],
        font=('Segoe UI', 11)
    )

    style.map('Sidebar.TButton',
        background=[('active', colors['hover'])]
    )

    # Configure label styles
    style.configure('SidebarTitle.TLabel',
        background=colors['sidebar'],
        foreground=colors['text'],
        font=('Segoe UI', 16, 'bold')
    )

    # Basic styles
    style.configure('TLabel', background='white')
    
    # Modern card style
    style.configure('Card.TFrame', 
        background='white',
        relief='groove',
        borderwidth=2,
        padding=15
    )
    
    # Modern header style
    style.configure('Header.TLabel',
        font=('Helvetica', 24, 'bold'),
        foreground='#2c3e50'
    )
    
    # Modern subheader style
    style.configure('Subheader.TLabel',
        font=('Helvetica', 16),
        foreground='#34495e'
    )
    
    # Button styles
    style.configure('info.Outline.TButton',
        font=('Helvetica', 11),
        padding=8,
        relief='flat',
        borderwidth=1
    )
    
    style.configure('success.TButton',
        font=('Helvetica', 11),
        padding=8,
        relief='flat'
    )
    
    # Sidebar styles
    style.configure('Sidebar.TFrame', 
        background='#1a237e',
        relief='flat'
    )
    
    style.configure('SidebarTitle.TLabel',
        font=('Helvetica', 20, 'bold'),
        foreground='white',
        background='#1a237e',
        padding=(10, 5)
    )
    
    # Tag style for labels
    style.configure('Tag.TLabel',
        background='#e9ecef',
        foreground='#2c3e50',
        padding=5,
        font=('Helvetica', 10),
        borderwidth=1,
        relief='solid'
    )
    
    # Location card style
    style.configure('LocationCard.TFrame',
        background='white',
        relief='solid',
        borderwidth=1,
        padding=15
    )
    
    # Time label style
    style.configure('Time.TLabel',
        font=('Helvetica', 12, 'bold'),
        foreground='#2980b9'
    )
    
    # Price label style
    style.configure('Price.TLabel',
        font=('Helvetica', 11),
        foreground='#27ae60'
    )

def configure_category_styles(style: Style, category_colors):
    for category, colors in category_colors.items():
        style.configure(
            f'Category.{category}.TFrame',
            background=colors['bg'],
            bordercolor=colors['accent']
        )
        
        style.configure(
            f'Category.{category}.TLabel',
            background=colors['bg'],
            foreground=colors['fg'],
            font=('Helvetica', 11)
        )
        
        style.configure(
            f'Category.{category}.Tag.TLabel',
            background=colors['accent'],
            foreground='white',
            padding=5,
            font=('Helvetica', 10, 'bold'),
            borderwidth=0
        )
