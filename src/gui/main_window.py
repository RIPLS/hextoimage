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

from core.hex_reader import read_file_as_hex_data, get_hex_summary
from core.analyzers import analyze_file_content, get_supported_file_types
from core.exporters import extract_detected_files, create_extraction_report
from core.formatters import format_hex_data, format_hex_summary


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
    """Widget for displaying detected files in a tree view."""
    
    def __init__(self, parent, preview_callback=None):
        super().__init__(parent)
        self.preview_callback = preview_callback
        self.detected_files = []
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the detected files UI."""
        # Create treeview with scrollbars
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview
        columns = ('Type', 'Size')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', height=10)
        
        # Configure columns
        self.tree.heading('#0', text='File')
        self.tree.heading('Type', text='Type')
        self.tree.heading('Size', text='Size')
        
        self.tree.column('#0', width=200, minwidth=150)
        self.tree.column('Type', width=120, minwidth=100)
        self.tree.column('Size', width=120, minwidth=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and treeview
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_file_select)
        
    def update_detected_files(self, detected_files: List[Any]):
        """Update the tree with detected files."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.detected_files = detected_files
        
        # Add detected files to tree
        for i, detected in enumerate(detected_files):
            file_name = f"File_{i+1}.{detected.signature.extension}"
            size_str = f"{detected.size:,} bytes" if detected.size else "Unknown"
            
            self.tree.insert('', 'end', text=file_name, values=(
                detected.file_type,
                size_str
            ))
            
    def on_file_select(self, event):
        """Handle file selection in tree."""
        selection = self.tree.selection()
        if selection and self.preview_callback:
            item = selection[0]
            index = self.tree.index(item)
            if 0 <= index < len(self.detected_files):
                self.preview_callback(self.detected_files[index])
                
    def clear_files(self):
        """Clear all detected files."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.detected_files = []


class MainWindow:
    """Main application window."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HexToImage - File Analysis Tool")
        self.root.geometry("900x700")
        self.root.minsize(600, 500)
        
        # Application state
        self.current_file_path = tk.StringVar()
        self.hex_data = None
        self.analysis_result = None
        self.is_analyzing = False
        
        self.setup_ui()
        self.setup_menu()
        
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
        content_frame = ttk.LabelFrame(parent, text="Analysis Results", padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create paned window for resizable sections
        paned = ttk.PanedWindow(content_frame, orient=tk.HORIZONTAL)
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
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
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
            command=self.analyze_file,
            style='Accent.TButton'
        )
        self.analyze_button.pack(side=tk.LEFT)
        
        # Right side - Settings and Help buttons
        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side=tk.RIGHT)
        
        self.help_button = ttk.Button(right_buttons, text="Help", command=self.show_help)
        self.help_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.settings_button = ttk.Button(right_buttons, text="Settings", command=self.show_settings)
        self.settings_button.pack(side=tk.RIGHT)
        
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
        else:
            # Even if no embedded files, show file information
            self._show_file_info()
            status = f"No embedded files detected - File size: {self.analysis_result.total_size:,} bytes"
            
        self.update_status(status)
        
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
        
    def show_settings(self):
        """Show settings dialog."""
        messagebox.showinfo("Settings", "Settings dialog not implemented yet.")
        
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
