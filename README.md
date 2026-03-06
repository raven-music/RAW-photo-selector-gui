# RAW-photo-selector-gui
A little GUI made in Python to make creating a selection of photos to import into your editing software easier. The GUI shows the JPEG of the image as the preview, but copies the RAW photo into a subdirectory.

### Note
The program prefers using JPEGs as the preview for performance. But if you only have RAW images, that's also supported. 

### Prerequisites
1. Keep the JPEGS and RAW images in the same directory. 
2. Install requirements: 
```
pip install -r requirements.txt
```

3. You might need to install tkinter if you are on Linux: 


```
apt install python3-tk
```

### Usage
1. Start the script:
    1. Either with the path as the argument: 
    ```
    python selector_gui.py C:\Path\To\Directory\Containing\RAW-photos
    ``` 

    2. Or without (it opens a file explorer window):
    ```
    python selector_gui.py
    ```

2. Navigate through the GUI using the arrow keys or the AWSD keys. Use up-arrow, the space bar, or w to like an image. 
3. A liked image gets copied into a sub-directory called 'selection'. 