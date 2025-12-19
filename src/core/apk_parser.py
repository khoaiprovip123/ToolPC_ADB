
import struct
import io
import zipfile

class APKParser:
    """
    A lightweight pure-python APK parser to extract basic information
    (package name, version, permissions) from binary AndroidManifest.xml
    without external dependencies like aapt.
    """
    
    # AXML Chunk Types
    RES_NULL_TYPE = 0x0000
    RES_STRING_POOL_TYPE = 0x0001
    RES_TABLE_TYPE = 0x0002
    RES_XML_TYPE = 0x0003
    
    # XML Chunk Types
    RES_XML_FIRST_CHUNK_TYPE = 0x0100
    RES_XML_START_NAMESPACE_TYPE = 0x0100
    RES_XML_END_NAMESPACE_TYPE = 0x0101
    RES_XML_START_ELEMENT_TYPE = 0x0102
    RES_XML_END_ELEMENT_TYPE = 0x0103
    RES_XML_CDATA_TYPE = 0x0104
    RES_XML_LAST_CHUNK_TYPE = 0x017f
    
    def __init__(self, apk_path):
        self.apk_path = apk_path
        self.strings = []
        self.package_name = "Unknown"
        self.version_code = "Unknown"
        self.version_name = "Unknown"
        self.permissions = []
        self.activities = []
        self.services = []
        self.receivers = []
        self.min_sdk = "Unknown"
        self.target_sdk = "Unknown"
        
    def parse(self):
        try:
            with zipfile.ZipFile(self.apk_path, 'r') as z:
                if 'AndroidManifest.xml' not in z.namelist():
                    return False
                
                with z.open('AndroidManifest.xml') as f:
                    data = f.read()
                    self._parse_axml(data)
                    return True
        except Exception as e:
            print(f"Error parsing APK: {e}")
            return False
            
    def _parse_axml(self, data):
        stream = io.BytesIO(data)
        
        # Header checking (AXML)
        header = struct.unpack('<I', stream.read(4))[0]
        if header != self.RES_XML_TYPE:
            # Maybe it's a raw xml? Unlikely for APK but possible
            return
            
        stream.read(4) # File size
        
        while stream.tell() < len(data):
            chunk_start = stream.tell()
            chunk_type = struct.unpack('<H', stream.read(2))[0]
            header_size = struct.unpack('<H', stream.read(2))[0]
            chunk_size = struct.unpack('<I', stream.read(4))[0]
            
            if chunk_type == self.RES_STRING_POOL_TYPE:
                self._parse_string_pool(stream, chunk_start)
            elif chunk_type == self.RES_XML_START_ELEMENT_TYPE:
                self._parse_start_element(stream, chunk_start)
            
            # Skip to next chunk
            stream.seek(chunk_start + chunk_size)
            
    def _parse_string_pool(self, stream, offset):
        stream.seek(offset + 8) # Skip common header
        string_count = struct.unpack('<I', stream.read(4))[0]
        style_count = struct.unpack('<I', stream.read(4))[0]
        flags = struct.unpack('<I', stream.read(4))[0]
        strings_start = struct.unpack('<I', stream.read(4))[0]
        styles_start = struct.unpack('<I', stream.read(4))[0]
        
        stream.seek(offset + strings_start + 8) # +8 for chunk header? No, strings_start is relative to chunk start
        # Re-calc absolute pos
        abs_strings_start = offset + strings_start
        
        # Read offsets
        offsets = []
        stream.seek(offset + 28) # Header size of String Pool is usually 28
        for _ in range(string_count):
            offsets.append(struct.unpack('<I', stream.read(4))[0])
            
        # Read strings
        for i in range(string_count):
            stream.seek(abs_strings_start + offsets[i])
            # 2 bytes length? Or 1? Depends on flags. UTF-8 flag is 1<<8
            # Standard AXML usually UTF-16LE
            
            if flags & (1 << 8): # UTF-8
                # Length is encoded in 1 or 2 bytes
                u16len = struct.unpack('B', stream.read(1))[0]
                if u16len & 0x80:
                    stream.read(1) # Skip high byte
                    
                u8len = struct.unpack('B', stream.read(1))[0]
                if u8len & 0x80:
                    stream.read(1)
                    
                s = stream.read(u8len).decode('utf-8', errors='ignore')
                self.strings.append(s)
            else: # UTF-16
                u16len = struct.unpack('<H', stream.read(2))[0]
                if u16len & 0x8000:
                    u16len = ((u16len & 0x7FFF) << 16) | struct.unpack('<H', stream.read(2))[0]
                    
                # Read u16len * 2 bytes
                s_bytes = stream.read(u16len * 2)
                s = s_bytes.decode('utf-16le', errors='ignore')
                self.strings.append(s)
                
    def _parse_start_element(self, stream, offset):
        stream.seek(offset + 8) # Skip chunk header
        line_no = struct.unpack('<I', stream.read(4))[0]
        comment_idx = struct.unpack('<I', stream.read(4))[0] # 0xFFFFFFFF = -1
        
        ns_idx = struct.unpack('<I', stream.read(4))[0]
        name_idx = struct.unpack('<I', stream.read(4))[0]
        
        attr_start = struct.unpack('<H', stream.read(2))[0]
        attr_size = struct.unpack('<H', stream.read(2))[0]
        attr_count = struct.unpack('<H', stream.read(2))[0]
        
        if name_idx >= len(self.strings): return
        tag_name = self.strings[name_idx]
        
        # Attributes
        stream.seek(offset + 36) # Position of attributes start usually
        # But should rely on header size 
        # Start Element chunk header size is 20 bytes (fixed) + 16 bytes (XML tree node) ?
        # Actually structure is:
        # header (8)
        # line_no (4)
        # comment (4)
        # ns (4)
        # name (4)
        # attr_start (2)
        # attr_size (2)
        # attr_count (2) 
        # id_index (2)
        # class_index (2)
        # style_index (2)
        
        stream.seek(offset + 36) # Move to attributes
        
        for i in range(attr_count):
            attr_ns_idx = struct.unpack('<I', stream.read(4))[0]
            attr_name_idx = struct.unpack('<I', stream.read(4))[0]
            attr_val_str_idx = struct.unpack('<I', stream.read(4))[0]
            attr_val_type = struct.unpack('<I', stream.read(4))[0] >> 24
            attr_val_data = struct.unpack('<I', stream.read(4))[0]
            
            if attr_name_idx >= len(self.strings): continue
            attr_name = self.strings[attr_name_idx]
            
            # Resolve Value
            attr_value = str(attr_val_data)
            if attr_val_str_idx != 0xFFFFFFFF and attr_val_str_idx < len(self.strings):
                attr_value = self.strings[attr_val_str_idx]
            
            # Processing Tags
            if tag_name == "manifest":
                if attr_name == "package":
                    self.package_name = attr_value
                elif attr_name == "versionCode":
                    self.version_code = attr_value
                elif attr_name == "versionName":
                    self.version_name = attr_value
                    
            elif tag_name == "uses-permission":
                if attr_name == "name":
                    self.permissions.append(attr_value)
                    
            elif tag_name == "uses-sdk":
                if attr_name == "minSdkVersion":
                    self.min_sdk = attr_value
                elif attr_name == "targetSdkVersion":
                    self.target_sdk = attr_value
            
            elif tag_name == "activity":
                if attr_name == "name":
                    self.activities.append(attr_value)
