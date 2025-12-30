"""
Script dọn dẹp các file thừa và tối ưu hóa dung lượng dự án
Author: Xiaomi ADB Commander Team
"""

import os
import shutil
import sys
from pathlib import Path

class ProjectCleaner:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.total_freed = 0
        self.deleted_files = []
        self.deleted_dirs = []
        
    def get_size(self, path):
        """Tính toán dung lượng của file hoặc thư mục"""
        if os.path.isfile(path):
            return os.path.getsize(path)
        elif os.path.isdir(path):
            total = 0
            try:
                for entry in os.scandir(path):
                    if entry.is_file(follow_symlinks=False):
                        total += entry.stat().st_size
                    elif entry.is_dir(follow_symlinks=False):
                        total += self.get_size(entry.path)
            except PermissionError:
                pass
            return total
        return 0
    
    def format_size(self, size_bytes):
        """Chuyển đổi bytes thành định dạng dễ đọc"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def clean_pycache(self):
        """Xóa tất cả thư mục __pycache__ và file .pyc"""
        print("\n🗑️  Đang dọn dẹp Python cache files...")
        
        # Tìm và xóa thư mục __pycache__
        for pycache_dir in self.project_root.rglob('__pycache__'):
            size = self.get_size(pycache_dir)
            try:
                shutil.rmtree(pycache_dir)
                self.total_freed += size
                self.deleted_dirs.append(str(pycache_dir.relative_to(self.project_root)))
                print(f"   ✓ Đã xóa: {pycache_dir.relative_to(self.project_root)} ({self.format_size(size)})")
            except Exception as e:
                print(f"   ✗ Lỗi khi xóa {pycache_dir}: {e}")
        
        # Tìm và xóa file .pyc
        for pyc_file in self.project_root.rglob('*.pyc'):
            size = self.get_size(pyc_file)
            try:
                pyc_file.unlink()
                self.total_freed += size
                self.deleted_files.append(str(pyc_file.relative_to(self.project_root)))
                print(f"   ✓ Đã xóa: {pyc_file.relative_to(self.project_root)} ({self.format_size(size)})")
            except Exception as e:
                print(f"   ✗ Lỗi khi xóa {pyc_file}: {e}")
    
    def clean_build_artifacts(self):
        """Xóa thư mục build và dist"""
        print("\n🗑️  Đang dọn dẹp build artifacts...")
        
        build_dirs = ['build', 'dist']
        for dir_name in build_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                size = self.get_size(dir_path)
                try:
                    shutil.rmtree(dir_path)
                    self.total_freed += size
                    self.deleted_dirs.append(dir_name)
                    print(f"   ✓ Đã xóa: {dir_name}/ ({self.format_size(size)})")
                except Exception as e:
                    print(f"   ✗ Lỗi khi xóa {dir_name}: {e}")
    
    def clean_logs(self):
        """Dọn dẹp file log"""
        print("\n🗑️  Đang dọn dẹp log files...")
        
        # Danh sách các file log cần xóa
        log_files = ['crash_log.txt', 'launch_log.txt']
        
        for log_file in log_files:
            log_path = self.project_root / log_file
            if log_path.exists():
                size = self.get_size(log_path)
                try:
                    log_path.unlink()
                    self.total_freed += size
                    self.deleted_files.append(log_file)
                    print(f"   ✓ Đã xóa: {log_file} ({self.format_size(size)})")
                except Exception as e:
                    print(f"   ✗ Lỗi khi xóa {log_file}: {e}")
        
        # Làm sạch app_log.txt (giữ lại 100 dòng cuối)
        app_log = self.project_root / 'logs' / 'app_log.txt'
        if app_log.exists():
            size_before = self.get_size(app_log)
            try:
                with open(app_log, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                if len(lines) > 100:
                    with open(app_log, 'w', encoding='utf-8') as f:
                        f.writelines(lines[-100:])
                    
                    size_after = self.get_size(app_log)
                    freed = size_before - size_after
                    self.total_freed += freed
                    print(f"   ✓ Đã làm sạch: logs/app_log.txt (tiết kiệm {self.format_size(freed)})")
            except Exception as e:
                print(f"   ✗ Lỗi khi làm sạch app_log.txt: {e}")
    
    def clean_debug_files(self):
        """Xóa các file debug tạm thời"""
        print("\n🗑️  Đang dọn dẹp debug files...")
        
        debug_patterns = ['debug_*.py']
        
        for pattern in debug_patterns:
            for debug_file in self.project_root.glob(pattern):
                size = self.get_size(debug_file)
                try:
                    debug_file.unlink()
                    self.total_freed += size
                    self.deleted_files.append(str(debug_file.relative_to(self.project_root)))
                    print(f"   ✓ Đã xóa: {debug_file.relative_to(self.project_root)} ({self.format_size(size)})")
                except Exception as e:
                    print(f"   ✗ Lỗi khi xóa {debug_file}: {e}")
    
    def print_summary(self):
        """In báo cáo tổng kết"""
        print("\n" + "="*60)
        print("📊 BÁO CÁO TỔng KẾT")
        print("="*60)
        print(f"✓ Tổng số thư mục đã xóa: {len(self.deleted_dirs)}")
        print(f"✓ Tổng số file đã xóa: {len(self.deleted_files)}")
        print(f"✓ Dung lượng đã tiết kiệm: {self.format_size(self.total_freed)}")
        print("="*60)
        
        if self.deleted_dirs:
            print("\n📁 Thư mục đã xóa:")
            for dir_name in self.deleted_dirs[:10]:  # Hiển thị tối đa 10
                print(f"   • {dir_name}")
            if len(self.deleted_dirs) > 10:
                print(f"   ... và {len(self.deleted_dirs) - 10} thư mục khác")
        
        if self.deleted_files:
            print("\n📄 File đã xóa:")
            for file_name in self.deleted_files[:10]:  # Hiển thị tối đa 10
                print(f"   • {file_name}")
            if len(self.deleted_files) > 10:
                print(f"   ... và {len(self.deleted_files) - 10} file khác")
    
    def run(self):
        """Chạy toàn bộ quá trình dọn dẹp"""
        print("🧹 BẮT ĐẦU DỌN DẸP DỰ ÁN")
        print(f"📁 Thư mục: {self.project_root}")
        print("="*60)
        
        self.clean_pycache()
        self.clean_build_artifacts()
        self.clean_logs()
        self.clean_debug_files()
        
        self.print_summary()
        print("\n✅ Hoàn thành dọn dẹp!")

def main():
    # Lấy đường dẫn thư mục gốc của dự án
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    cleaner = ProjectCleaner(project_root)
    cleaner.run()

if __name__ == "__main__":
    main()
