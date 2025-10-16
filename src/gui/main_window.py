#!/usr/bin/env python3
"""
Main GUI window for HexToImage application.

This module provides a modern graphical interface for analyzing hex files
and detecting embedded files with preview capabilities.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import tempfile
import io

# Optional PIL import for image preview
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.hex_reader import read_file_as_hex_data, get_hex_summary
from src.core.analyzers import analyze_file_content, get_supported_file_types
from src.core.exporters import extract_detected_files, create_extraction_report
from src.core.formatters import format_hex_data, format_hex_summary


class FilePreviewWidget(ttk.Frame):
    """Widget for displaying file previews."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the preview UI components."""
        # Simple image preview frame (no tabs)
        self.image_frame = ttk.Frame(self)
        self.image_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Image preview label
        self.image_label = ttk.Label(self.image_frame, text="No preview available")
        self.image_label.pack(expand=True)
        
    def show_image_preview(self, image_data: bytes):
        """Show image preview."""
        if not PIL_AVAILABLE:
            error_msg = """Image preview requires Pillow

To enable image preview, install Pillow:
pip3 install Pillow

Then restart the application.

File size: {:.1f} KB
Data available for preview""".format(len(image_data) / 1024)
            self.image_label.configure(image="", text=error_msg)
            return
            
        try:
            # Clear any existing image first
            if hasattr(self.image_label, 'image'):
                self.image_label.image = None
            self.image_label.configure(image="", text="Loading image...")
            
            # Load and validate the image first
            image = Image.open(io.BytesIO(image_data))
            original_size = image.size
            original_format = image.format
            
            # Resize image to fit preview while maintaining aspect ratio
            image.thumbnail((400, 400), Image.Resampling.LANCZOS)
            
            try:
                # Try to create and display the PhotoImage
                photo = ImageTk.PhotoImage(image)
                
                # Set the image and keep the reference
                self.image_label.configure(image=photo, text="")
                self.image_label.image = photo  # Keep a reference to prevent garbage collection
                
            except (tk.TclError, RuntimeError) as display_error:
                # Fallback: show image information instead of the actual image
                info_text = f"""✅ Image Successfully Loaded

Format: {original_format}
Original Size: {original_size[0]} x {original_size[1]} pixels
Thumbnail Size: {image.size[0]} x {image.size[1]} pixels
File Size: {len(image_data):,} bytes

Image is valid and ready for display.
(GUI display limitation: {str(display_error)})"""
                self.image_label.configure(image="", text=info_text)
            
        except Exception as e:
            # Clear image and show error
            if hasattr(self.image_label, 'image'):
                self.image_label.image = None
            self.image_label.configure(image="", text=f"Cannot display image: {str(e)}")
            
    def show_error(self, error_message: str):
        """Show error message in preview."""
        self.image_label.configure(image="", text=f"Error: {error_message}")
            
    def clear_preview(self):
        """Clear all previews."""
        # Clear image reference first
        if hasattr(self.image_label, 'image'):
            self.image_label.image = None
        self.image_label.configure(image="", text="No preview available")


class DetectedFilesWidget(ttk.Frame):
    """Widget for displaying detected files with checkboxes."""
    
    def __init__(self, parent, preview_callback=None):
        super().__init__(parent)
        self.preview_callback = preview_callback
        self.detected_files = []
        self.selected_files = set()  # Track selected files by index
        self.checkbuttons = []  # Store checkbutton widgets
        self.check_vars = []  # Store checkbox variables
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the detected files UI with custom checkboxes."""
        # Main container
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self._create_header(container)
        
        # Separator after header
        ttk.Separator(container, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 5))
        
        # Create a frame for the scrollable content
        scroll_container = ttk.Frame(container)
        scroll_container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas for scrolling
        self.canvas = tk.Canvas(scroll_container, bg='white', highlightthickness=0)
        self.v_scrollbar = ttk.Scrollbar(scroll_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self._update_scrollregion()
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)
        
        # Bind canvas width to scrollable frame width
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        # Pack canvas (scrollbar will be packed/unpacked dynamically)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind mouse wheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
    def _on_canvas_configure(self, event):
        """Handle canvas resize."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self._update_scrollregion()
        
    def _update_scrollregion(self):
        """Update scroll region and manage scrollbar visibility."""
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        
        if bbox:
            content_height = bbox[3] - bbox[1]
            canvas_height = self.canvas.winfo_height()
            
            # Configure scrollregion
            self.canvas.configure(scrollregion=bbox)
            
            # Show/hide scrollbar based on content
            if content_height > canvas_height:
                # Content exceeds viewport - enable scrolling
                self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            else:
                # Content fits in viewport - hide scrollbar and reset position
                self.v_scrollbar.pack_forget()
                self.canvas.yview_moveto(0)  # Reset to top
        else:
            self.canvas.configure(scrollregion=(0, 0, 0, 0))
            self.v_scrollbar.pack_forget()
        
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling when mouse is over the file list."""
        # Check if mouse is over the canvas or scrollable frame
        widget_under_mouse = self.canvas.winfo_containing(event.x_root, event.y_root)
        
        # Allow scrolling if mouse is over the canvas or any child widget
        if widget_under_mouse and (widget_under_mouse == self.canvas or 
                                   str(widget_under_mouse).startswith(str(self.scrollable_frame))):
            # Check if content height exceeds canvas height
            bbox = self.canvas.bbox("all")
            if bbox:
                content_height = bbox[3] - bbox[1]
                canvas_height = self.canvas.winfo_height()
                # Only scroll if content is larger than viewport
                if content_height > canvas_height:
                    self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            
    def _create_header(self, parent):
        """Create table header."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Header style
        header_style = {'font': ('TkDefaultFont', 9, 'bold'), 'anchor': tk.W}
        
        # Checkbox column (empty header)
        ttk.Label(header_frame, text='', width=5).grid(row=0, column=0, padx=(5, 0), sticky=tk.W)
        # File column
        ttk.Label(header_frame, text='File', **header_style).grid(row=0, column=1, padx=10, sticky=tk.W)
        # Type column
        ttk.Label(header_frame, text='Type', width=15, **header_style).grid(row=0, column=2, padx=10, sticky=tk.W)
        # Size column
        ttk.Label(header_frame, text='Size', width=15, **header_style).grid(row=0, column=3, padx=10, sticky=tk.W)
        
        # Configure column weights
        header_frame.columnconfigure(1, weight=1)
        
    def update_detected_files(self, detected_files: List[Any]):
        """Update the list with detected files."""
        # Clear existing items
        for widget in self.checkbuttons:
            widget.destroy()
        self.checkbuttons.clear()
        self.check_vars.clear()
            
        self.detected_files = detected_files
        self.selected_files.clear()
        
        # Add detected files with checkboxes
        for i, detected in enumerate(detected_files):
            file_name = f"File_{i+1}.{detected.signature.extension}"
            size_str = f"{detected.size:,} bytes" if detected.size else "Unknown"
            
            # Create row frame
            row_frame = ttk.Frame(self.scrollable_frame)
            row_frame.pack(fill=tk.X, pady=2)
            
            # Store the frame for later cleanup
            self.checkbuttons.append(row_frame)
            
            # Create checkbox variable
            check_var = tk.BooleanVar(value=False)
            self.check_vars.append(check_var)
            
            # Checkbox
            checkbox = ttk.Checkbutton(
                row_frame, 
                variable=check_var,
                command=lambda idx=i: self._on_checkbox_toggle(idx)
            )
            checkbox.grid(row=0, column=0, padx=(5, 0), sticky=tk.W)
            
            # File name (clickable for preview)
            file_label = ttk.Label(row_frame, text=file_name, cursor='hand2')
            file_label.grid(row=0, column=1, padx=10, sticky=tk.W)
            file_label.bind('<Button-1>', lambda e, idx=i: self._on_file_click(idx))
            
            # Type
            type_label = ttk.Label(row_frame, text=detected.file_type, width=15)
            type_label.grid(row=0, column=2, padx=10, sticky=tk.W)
            
            # Size
            size_label = ttk.Label(row_frame, text=size_str, width=15)
            size_label.grid(row=0, column=3, padx=10, sticky=tk.W)
            
            # Configure column weights
            row_frame.columnconfigure(1, weight=1)
            
            # Hover effect
            def on_enter(e, frame=row_frame):
                frame.configure(style='Hover.TFrame')
            def on_leave(e, frame=row_frame):
                frame.configure(style='TFrame')
                
            for widget in [row_frame, file_label, type_label, size_label]:
                widget.bind('<Enter>', on_enter)
                widget.bind('<Leave>', on_leave)
        
        # Update scroll region after adding all files
        self.canvas.after(100, self._update_scrollregion)
                
    def _on_checkbox_toggle(self, index):
        """Handle checkbox toggle."""
        if self.check_vars[index].get():
            self.selected_files.add(index)
        else:
            self.selected_files.discard(index)
            
    def _on_file_click(self, index):
        """Handle file name click for preview."""
        if self.preview_callback and 0 <= index < len(self.detected_files):
            self.preview_callback(self.detected_files[index])
                    
    def get_selected_files(self):
        """Get list of selected detected files."""
        return [self.detected_files[i] for i in sorted(self.selected_files)]
        
    def clear_files(self):
        """Clear all detected files."""
        for widget in self.checkbuttons:
            widget.destroy()
        self.checkbuttons.clear()
        self.check_vars.clear()
        self.detected_files = []
        self.selected_files.clear()
        
        # Hide scrollbar when there's no content
        self.canvas.after(100, self._update_scrollregion)


class MainWindow:
    """Main application window."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HexToImage - File Analysis Tool")
        self.root.geometry("900x700")
        self.root.minsize(600, 500)
        
        # Set application icon
        self.set_app_icon()
        
        # Application state
        self.current_file_path = tk.StringVar()
        self.hex_data = None
        self.analysis_result = None
        self.is_analyzing = False
        self.is_exporting = False
        
        self.setup_ui()
        self.setup_menu()
        
    def set_app_icon(self):
        """Set the application icon."""
        try:
            # Get the base assets path
            assets_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'assets')
            assets_dir = os.path.abspath(assets_dir)
            
            # For Windows - try to use .ico first, then convert .png if needed
            if sys.platform == 'win32':
                # Try .ico file first
                ico_path = os.path.join(assets_dir, 'icon.ico')
                png_path = os.path.join(assets_dir, 'icon.png')
                
                if os.path.exists(ico_path):
                    try:
                        self.root.iconbitmap(ico_path)
                    except Exception as ico_error:
                        print(f"Could not set .ico icon: {ico_error}")
                        # Fallback to PNG with iconphoto
                        if os.path.exists(png_path):
                            try:
                                icon_img = tk.PhotoImage(file=png_path)
                                self.root.iconphoto(True, icon_img)
                            except Exception as png_error:
                                print(f"Could not set .png icon: {png_error}")
                elif os.path.exists(png_path):
                    # Use PNG with iconphoto (works in Windows 10+)
                    try:
                        icon_img = tk.PhotoImage(file=png_path)
                        self.root.iconphoto(True, icon_img)
                        
                        # For Windows taskbar icon, we need to set the appid
                        try:
                            import ctypes
                            myappid = 'hextoimage.fileanalyzer.1.0.0'
                            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                        except Exception as appid_error:
                            print(f"Could not set Windows AppUserModelID: {appid_error}")
                    except Exception as png_error:
                        print(f"Could not set .png icon: {png_error}")
                else:
                    print(f"Icon files not found in: {assets_dir}")
                    
            # For macOS and Linux
            elif sys.platform == 'darwin' or sys.platform.startswith('linux'):
                png_path = os.path.join(assets_dir, 'icon.png')
                if os.path.exists(png_path):
                    icon_img = tk.PhotoImage(file=png_path)
                    self.root.iconphoto(True, icon_img)
                else:
                    print(f"Icon file not found: {png_path}")
                    
        except Exception as e:
            print(f"Could not set application icon: {e}")
        
    def setup_menu(self):
        """Setup the application menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open...", command=self.browse_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.browse_file())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        
    def setup_ui(self):
        """Setup the main user interface."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # File selection section
        self.setup_file_section(main_frame)
        
        # Main content area with preview
        self.setup_content_section(main_frame)
        
        # Progress bar
        self.setup_progress_section(main_frame)
        
        # Button section
        self.setup_button_section(main_frame)
        
    def setup_file_section(self, parent):
        """Setup file selection section."""
        file_frame = ttk.LabelFrame(parent, text="File Selection", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # File path entry and browse button
        path_frame = ttk.Frame(file_frame)
        path_frame.pack(fill=tk.X)
        
        ttk.Label(path_frame, text="File:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.file_entry = ttk.Entry(path_frame, textvariable=self.current_file_path)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.file_entry.bind('<Return>', self.on_file_path_enter)
        self.file_entry.bind('<FocusOut>', self.on_file_path_change)
        
        button_frame = ttk.Frame(path_frame)
        button_frame.pack(side=tk.RIGHT)
        
        self.browse_button = ttk.Button(button_frame, text="Browse...", command=self.browse_file)
        self.browse_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.manual_button = ttk.Button(button_frame, text="Manual", command=self.manual_file_entry)
        self.manual_button.pack(side=tk.LEFT)
        
    def setup_content_section(self, parent):
        """Setup main content section with detected files and preview."""
        # Create notebook (tabbed interface) directly at parent level
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Tab 1: RESULT (Detected files + Preview)
        self.result_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.result_tab, text="Results")
        
        # Add padding to the result tab
        result_inner = ttk.Frame(self.result_tab, padding=10)
        result_inner.pack(fill=tk.BOTH, expand=True)
        
        # Create paned window for resizable sections
        paned = ttk.PanedWindow(result_inner, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Detected files
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=2)
        
        ttk.Label(left_frame, text="Detected Files:", font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        self.detected_files_widget = DetectedFilesWidget(left_frame, self.preview_file)
        self.detected_files_widget.pack(fill=tk.BOTH, expand=True)
        
        # Right panel - Preview
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        ttk.Label(right_frame, text="File Preview:", font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        self.preview_widget = FilePreviewWidget(right_frame)
        self.preview_widget.pack(fill=tk.BOTH, expand=True)
        
        # Tab 2: HEX VIEWER (Hexadecimal content)
        self.hex_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.hex_tab, text="Hex Viewer")
        
        self.setup_hex_viewer(self.hex_tab)
        
    def setup_hex_viewer(self, parent):
        """Setup the hexadecimal viewer interface."""
        # Create frame for hex viewer
        hex_frame = ttk.Frame(parent, padding=5)
        hex_frame.pack(fill=tk.BOTH, expand=True)
        
        # Info label
        ttk.Label(hex_frame, text="Hexadecimal Content:", font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        # Hex text display with scrollbars
        text_frame = ttk.Frame(hex_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(text_frame)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scrollbar = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Text widget with monospace font
        self.hex_text = tk.Text(
            text_frame,
            wrap=tk.NONE,
            font=('Courier', 10),
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            bg='#f0f0f0',
            fg='#000000',
            padx=5,
            pady=5
        )
        self.hex_text.pack(fill=tk.BOTH, expand=True)
        
        v_scrollbar.config(command=self.hex_text.yview)
        h_scrollbar.config(command=self.hex_text.xview)
        
        # Make text read-only
        self.hex_text.config(state=tk.DISABLED)
        
    def setup_progress_section(self, parent):
        """Setup progress bar section."""
        progress_frame = ttk.Frame(parent)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var, 
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.BOTH, expand=True)
        
        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.pack(anchor=tk.W)
        
    def setup_button_section(self, parent):
        """Setup button section."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X)
        
        # Left side - Analyze button
        self.analyze_button = ttk.Button(
            button_frame, 
            text="Analyze", 
            command=self.analyze_file
        )
        self.analyze_button.pack(side=tk.LEFT)
        
        # Center - Export button
        self.export_button = ttk.Button(
            button_frame,
            text="Export Selected",
            command=self.export_selected_files,
            state='disabled'
        )
        self.export_button.pack(side=tk.LEFT, padx=(10, 0))
        
        # Right side - Settings and Help buttons
        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side=tk.RIGHT)
        
        self.help_button = ttk.Button(right_buttons, text="Help", command=self.show_help)
        self.help_button.pack(side=tk.RIGHT, padx=(10, 0))
        
    def browse_file(self):
        """Open file browser dialog with macOS compatibility."""
        import platform
        import os
        
        # Detect if we're on macOS
        is_macos = platform.system() == "Darwin"
        
        if is_macos:
            # macOS-specific approach: Use the most permissive settings
            try:
                # On macOS, we need to be very specific about file types
                # The trick is to not use any filters at all for maximum compatibility
                file_path = filedialog.askopenfilename(
                    title="Select any file to analyze",
                    # Don't specify filetypes on macOS - let it show everything
                )
                
                # If that doesn't work, try with a single permissive filter
                if not file_path:
                    file_path = filedialog.askopenfilename(
                        title="Select file to analyze",
                        filetypes=[("All files", "*.*")]
                    )
                    
            except Exception as e:
                print(f"macOS file dialog error: {e}")
                # Show instructions for manual entry
                messagebox.showinfo(
                    "File Selection Issue",
                    "The file browser may have restrictions on macOS.\n\n"
                    "Please use the 'Manual' button to enter the file path directly,\n"
                    "or drag and drop the file into the path field."
                )
                return
        else:
            # Non-macOS systems: Use the full filter list
            try:
                file_path = filedialog.askopenfilename(
                    title="Select any file to analyze",
                    filetypes=[
                        ("All files", "*"),
                        ("All files with extensions", "*.*"),
                        ("Binary files", "*.bin *.dat *.raw"),
                        ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tiff"),
                        ("Document files", "*.pdf *.doc *.docx *.txt"),
                        ("Archive files", "*.zip *.rar *.7z *.tar *.gz"),
                        ("Executable files", "*.exe *.dll *.so *.dylib"),
                        ("Database files", "*.db *.sqlite *.mdb"),
                        ("Media files", "*.mp3 *.mp4 *.avi *.mkv *.wav"),
                        ("System files", "*.sys *.log *.tmp *.cache"),
                    ],
                    initialdir=".",
                    defaultextension=""
                )
            except Exception as e:
                print(f"File dialog error: {e}")
                file_path = filedialog.askopenfilename(
                    title="Select file to analyze",
                    filetypes=[("All files", "*.*")]
                )
        
        if file_path:
            self.current_file_path.set(file_path)
            self.clear_results()
            
    def manual_file_entry(self):
        """Enable manual file path entry."""
        import platform
        
        if platform.system() == "Darwin":  # macOS
            message = """Manual File Entry for macOS

You can type or paste the file path directly in the text field.

This is especially useful on macOS for:
• Files without extensions (like 'thumbdata5', 'Makefile')
• Hidden files (like '.bashrc', '.DS_Store')
• System files that the browser can't access
• Files in restricted directories

Examples of valid paths:
• ./filename_without_extension
• ~/Documents/my_file
• /Users/your_username/Desktop/data
• /tmp/temporary_file

Press Enter after typing the path, or click elsewhere to validate."""
        else:
            message = """Manual File Entry

You can type or paste the file path directly in the text field.

This is useful for:
• Files without extensions
• Hidden files
• Files in system directories
• Any file the browser can't select

Press Enter after typing the path."""
        
        messagebox.showinfo("Manual File Entry", message)
        self.file_entry.focus_set()
        
    def on_file_path_enter(self, event):
        """Handle Enter key in file path entry."""
        self.validate_and_set_file_path()
        
    def on_file_path_change(self, event):
        """Handle focus out from file path entry."""
        self.validate_and_set_file_path()
        
    def validate_and_set_file_path(self):
        """Validate and set the file path from manual entry."""
        file_path = self.current_file_path.get().strip()
        if file_path:
            # Expand user path (~) and resolve relative paths
            import os
            file_path = os.path.expanduser(file_path)
            file_path = os.path.abspath(file_path)
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self.current_file_path.set(file_path)
                self.clear_results()
                self.update_status(f"File selected: {os.path.basename(file_path)}")
            elif file_path != "":  # Only show error if user actually entered something
                self.show_error(f"File not found: {file_path}")
            
    def on_click(self, event):
        """Handle click events (fallback for drag and drop)."""
        # This is a basic fallback - not full drag and drop
        pass
                
    def clear_results(self):
        """Clear all analysis results."""
        self.detected_files_widget.clear_files()
        self.preview_widget.clear_preview()
        self.hex_data = None
        self.analysis_result = None
        self.update_status("Ready")
        
        # Disable export button when no results
        self.export_button.configure(state='disabled')
        
        # Clear hex viewer
        if hasattr(self, 'hex_text'):
            self.hex_text.configure(state=tk.NORMAL)
            self.hex_text.delete(1.0, tk.END)
            self.hex_text.configure(state=tk.DISABLED)
        
    def analyze_file(self):
        """Analyze the selected file."""
        if not self.current_file_path.get():
            messagebox.showwarning("No File Selected", "Please select a file to analyze.")
            return
            
        if self.is_analyzing:
            return
            
        # Start analysis in background thread
        self.is_analyzing = True
        self.analyze_button.configure(state='disabled', text='Analyzing...')
        
        thread = threading.Thread(target=self._analyze_file_thread, daemon=True)
        thread.start()
        
    def _analyze_file_thread(self):
        """Background thread for file analysis."""
        try:
            file_path = self.current_file_path.get()
            
            # Update progress
            self.root.after(0, lambda: self.update_progress(10, "Reading file..."))
            
            # Read hex data
            self.hex_data = read_file_as_hex_data(file_path)
            if not self.hex_data:
                raise Exception("Failed to read file")
                
            self.root.after(0, lambda: self.update_progress(30, "Analyzing file content..."))
            
            # Analyze file content
            self.analysis_result = analyze_file_content(self.hex_data)
            
            self.root.after(0, lambda: self.update_progress(80, "Processing results..."))
            
            # Update UI with results
            self.root.after(0, self._update_analysis_results)
            
            self.root.after(0, lambda: self.update_progress(100, "Analysis complete"))
            
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            self.root.after(0, lambda: self.show_error(error_msg))
        finally:
            self.root.after(0, self._analysis_complete)
            
    def _update_analysis_results(self):
        """Update UI with analysis results."""
        if self.analysis_result and self.analysis_result.detected_files:
            self.detected_files_widget.update_detected_files(self.analysis_result.detected_files)
            status = f"Found {len(self.analysis_result.detected_files)} embedded files"
            # Enable export button when files are detected
            self.export_button.configure(state='normal')
        else:
            # Even if no embedded files, show file information
            self._show_file_info()
            status = f"No embedded files detected - File size: {self.analysis_result.total_size:,} bytes"
            # Disable export button when no files detected
            self.export_button.configure(state='disabled')
            
        self.update_status(status)
        
        # Update hex viewer with file content
        self.update_hex_viewer()
        
    def _show_file_info(self):
        """Show basic file information when no embedded files are detected."""
        if not self.hex_data or not self.analysis_result:
            return
            
        # Create a fake "detected file" entry for the original file
        import os
        file_path = self.current_file_path.get()
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lstrip('.')
        
        # Create a basic file info entry
        file_info = type('FileInfo', (), {
            'file_type': f'{file_ext.upper() if file_ext else "BINARY"}',
            'start_offset': 0,
            'end_offset': self.analysis_result.total_size,
            'size': self.analysis_result.total_size,
            'signature': type('Signature', (), {
                'extension': file_ext or 'bin',
                'description': f'Original file: {file_name}'
            })(),
            'confidence': 1.0
        })()
        
        # Show in the detected files widget
        self.detected_files_widget.update_detected_files([file_info])
        
    def _analysis_complete(self):
        """Clean up after analysis completion."""
        self.is_analyzing = False
        self.analyze_button.configure(state='normal', text='Analyze')
        self.progress_var.set(0)
        
    def export_selected_files(self):
        """Export selected files to user-chosen location."""
        if self.is_exporting:
            return
            
        # Get selected files
        selected_files = self.detected_files_widget.get_selected_files()
        if not selected_files:
            messagebox.showwarning("No Files Selected", "Please select files to export by checking the boxes.")
            return
            
        # Ask user for output directory
        output_dir = filedialog.askdirectory(
            title="Select Export Location",
            initialdir="."
        )
        
        if not output_dir:
            return
            
        # Start export in background thread
        self.is_exporting = True
        self.export_button.configure(state='disabled', text='Exporting...')
        self.analyze_button.configure(state='disabled')
        self.browse_button.configure(state='disabled')
        
        thread = threading.Thread(target=self._export_files_thread, args=(selected_files, output_dir), daemon=True)
        thread.start()
        
    def _export_files_thread(self, selected_files, output_dir):
        """Background thread for file export."""
        try:
            self.root.after(0, lambda: self.update_progress(10, "Preparing export..."))
            
            # Create a temporary analysis result with only selected files
            temp_analysis_result = type('AnalysisResult', (), {
                'source_file': self.current_file_path.get(),
                'detected_files': selected_files
            })()
            
            self.root.after(0, lambda: self.update_progress(30, "Extracting files..."))
            
            # Use the existing export functionality
            from src.core.exporters import extract_detected_files
            
            # Extract files
            extraction_result = extract_detected_files(
                self.hex_data,
                temp_analysis_result,
                output_dir=output_dir,
                clean_existing=False
            )
            
            self.root.after(0, lambda: self.update_progress(80, "Finalizing export..."))
            
            # Show completion message
            success_msg = f"Export completed!\n\n"
            success_msg += f"Files exported: {extraction_result.total_extracted}\n"
            success_msg += f"Location: {extraction_result.output_directory}\n"
            success_msg += f"Success rate: {extraction_result.success_rate:.1%}"
            
            if extraction_result.failed_extractions:
                success_msg += f"\n\nFailed extractions: {len(extraction_result.failed_extractions)}"
                
            self.root.after(0, lambda: self._export_complete(success_msg))
            
        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            self.root.after(0, lambda: self._export_complete(error_msg, is_error=True))
        finally:
            self.root.after(0, self._export_cleanup)
            
    def _export_complete(self, message, is_error=False):
        """Handle export completion."""
        if is_error:
            messagebox.showerror("Export Error", message)
        else:
            messagebox.showinfo("Export Complete", message)
            
    def _export_cleanup(self):
        """Clean up after export completion."""
        self.is_exporting = False
        self.export_button.configure(state='normal', text='Export Selected')
        self.analyze_button.configure(state='normal')
        self.browse_button.configure(state='normal')
        self.progress_var.set(0)
        self.update_status("Export completed")
        
    def preview_file(self, detected_file):
        """Preview a detected file."""
        if not self.hex_data or not detected_file:
            self.preview_widget.show_error("No file data available")
            return
            
        try:
            # Extract file data
            start = detected_file.start_offset
            end = detected_file.end_offset or (start + (detected_file.size or 8192))
            
            # Get raw bytes from hex data with robust error handling
            file_data = bytes()
            
            # More precise extraction for embedded files
            bytes_needed = end - start
            bytes_extracted = 0
            
            for line in self.hex_data.lines:
                try:
                    # Check if this line contains data we need
                    line_end = line.offset + len(line.raw_bytes) if hasattr(line, 'raw_bytes') and line.raw_bytes else line.offset + 16
                    
                    if line.offset < end and line_end > start:
                        # Calculate the exact bytes we need from this line
                        extract_start = max(0, start - line.offset)
                        extract_end = min(len(line.raw_bytes) if hasattr(line, 'raw_bytes') and line.raw_bytes else 16, 
                                        end - line.offset)
                        
                        if extract_end > extract_start:
                            # Method 1: Use raw_bytes directly (preferred)
                            if hasattr(line, 'raw_bytes') and line.raw_bytes:
                                chunk = line.raw_bytes[extract_start:extract_end]
                                file_data += chunk
                                bytes_extracted += len(chunk)
                            
                            # Method 2: Reconstruct from hex_bytes (fallback)
                            elif hasattr(line, 'hex_bytes') and line.hex_bytes:
                                for i in range(extract_start, min(extract_end, len(line.hex_bytes))):
                                    if i < len(line.hex_bytes) and line.hex_bytes[i] is not None:
                                        file_data += bytes([line.hex_bytes[i]])
                                        bytes_extracted += 1
                    
                    # Stop if we have enough data
                    if bytes_extracted >= bytes_needed:
                        break
                        
                except Exception as line_error:
                    # Skip problematic lines but continue processing
                    continue
                            
            # Smart preview size limit based on file type and size
            if detected_file.file_type.lower() in ['jpeg', 'jpg', 'png', 'gif', 'bmp', 'webp', 'tiff']:
                # For image files, use more data or full file if it's small enough
                if len(file_data) <= 5 * 1024 * 1024:  # 5MB limit for full images
                    preview_data = file_data  # Use full image data
                else:
                    preview_data = file_data[:512 * 1024]  # 512KB for large images
            else:
                # For non-image files, use smaller preview
                preview_data = file_data[:min(len(file_data), 16384)]
            
            # Validate and show preview
            if len(preview_data) > 0:
                # Additional validation for image files
                if detected_file.file_type.lower() in ['jpeg', 'jpg', 'png', 'gif', 'bmp', 'webp', 'tiff']:
                    # Check if we have the expected file signature
                    signature_valid = False
                    if detected_file.file_type.lower() in ['jpeg', 'jpg'] and preview_data.startswith(b'\xFF\xD8\xFF'):
                        signature_valid = True
                    elif detected_file.file_type.lower() == 'png' and preview_data.startswith(b'\x89PNG\r\n\x1a\n'):
                        signature_valid = True
                    elif detected_file.file_type.lower() == 'gif' and preview_data.startswith(b'GIF8'):
                        signature_valid = True
                    else:
                        signature_valid = True  # For other formats, try anyway
                    
                    if not signature_valid:
                        self.preview_widget.show_error(f"Invalid {detected_file.file_type} signature in extracted data")
                        return
                
                try:
                    self.preview_widget.show_image_preview(preview_data)
                except Exception as img_error:
                    # Enhanced error info for debugging
                    error_msg = f"Cannot display as image: {str(img_error)}\n\n"
                    error_msg += f"File: {detected_file.file_type}\n"
                    error_msg += f"Expected size: {detected_file.size:,} bytes\n"
                    error_msg += f"Extracted size: {len(file_data):,} bytes\n"
                    error_msg += f"Preview size: {len(preview_data):,} bytes\n"
                    error_msg += f"First 20 bytes: {preview_data[:20].hex()}"
                    self.preview_widget.show_error(error_msg)
            else:
                self.preview_widget.show_error("No data extracted for preview")
                
        except Exception as e:
            # Enhanced error reporting
            import traceback
            error_details = f"Preview error: {str(e)}\n\nDetails:\n{traceback.format_exc()}"
            self.preview_widget.show_error(error_details)
            
    def update_hex_viewer(self):
        """Update the hexadecimal viewer with the current hex_data."""
        if not self.hex_data:
            self.hex_text.configure(state=tk.DISABLED)
            self.hex_text.delete(1.0, tk.END)
            return

        # Clear existing content
        self.hex_text.configure(state=tk.NORMAL)
        self.hex_text.delete(1.0, tk.END)

        # Format and insert hex data
        formatted_hex = format_hex_data(self.hex_data)
        self.hex_text.insert(tk.END, formatted_hex)

        # Scroll to the beginning
        self.hex_text.see(tk.END)
        self.hex_text.configure(state=tk.DISABLED)

    def update_progress(self, value: float, status: str):
        """Update progress bar and status."""
        self.progress_var.set(value)
        self.update_status(status)
        
    def update_status(self, status: str):
        """Update status label."""
        self.status_label.configure(text=status)
        
    def show_error(self, message: str):
        """Show error message."""
        messagebox.showerror("Error", message)
        self.update_status("Error occurred")
        
    def show_help(self):
        """Show help dialog."""
        help_text = """HexToImage - Universal File Analysis Tool

This tool can analyze ANY file type to:
• Display hexadecimal content
• Detect embedded files by their signatures
• Provide file previews
• Analyze binary structure and patterns

How to use:
1. Select a file using one of these methods:
   • Click 'Browse...' to use the file dialog or type the file path directly
2. Click 'Analyze' to scan the file
3. View detected files or original file information
4. Select items to preview content with intelligent formatting

Features:
• Universal file support (executables, images, documents, etc.)
• Automatic text/binary detection
• Enhanced hex viewer with analysis
• Image preview (when Pillow is installed)
• File entropy and pattern analysis

Embedded file detection for: """ + ", ".join(get_supported_file_types())
        
        messagebox.showinfo("Help", help_text)
        
    def show_about(self):
        """Show about dialog."""
        about_text = """HexToImage v1.0.0

A tool for analyzing hex data and detecting embedded files.

Features:
- File signature detection
- Preview capabilities
- Modern GUI interface
- Export functionality

Built with Python and tkinter."""
        
        messagebox.showinfo("About", about_text)
        
    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    """Main entry point for GUI application."""
    try:
        app = MainWindow()
        app.run()
    except Exception as e:
        print(f"Failed to start GUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
