def configure_styles(style: Style):
    # Sidebar styles
    style.configure('Sidebar.TFrame',
        background='#2c3e50',
        relief='flat'
    )
    
    style.configure('Sidebar.TButton',
        font=('Helvetica', 11),
        padding=15,
        background='#2c3e50',
        foreground='white'
    )
    
    style.map('Sidebar.TButton',
        background=[('active', '#34495e')],
        foreground=[('active', 'white')]
    )