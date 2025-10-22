import os
import csv
import json
from pathlib import Path
from typing import List, Dict

def identify_disaster_type(directory_name: str) -> str:
    """
    Identify disaster type from directory name.
    
    Args:
        directory_name: Name of the subdirectory
        
    Returns:
        Disaster type as string (earthquake, hurricane, flood, wildfire, or unknown)
    """
    dir_lower = directory_name.lower()
    
    if 'earthquake' in dir_lower:
        return 'earthquake'
    elif 'hurricane' in dir_lower:
        return 'hurricane'
    elif 'flood' in dir_lower:
        return 'flood'
    elif 'wildfire' in dir_lower or 'fire' in dir_lower:
        return 'wildfire'
    else:
        return 'unknown'

def tsv_to_jsonl(tsv_path: str, disaster_type: str) -> List[Dict]:
    """
    Convert TSV file to list of dictionaries with disaster type added.
    
    Args:
        tsv_path: Path to TSV file
        disaster_type: Type of disaster to add to each entry
        
    Returns:
        List of dictionaries representing JSONL entries
    """
    entries = []
    
    with open(tsv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            # Add disaster type to each entry
            row['disaster'] = disaster_type
            entries.append(row)
    
    return entries

def process_directory(base_path: str, output_dir: str = None):
    """
    Process all subdirectories and combine TSV files into JSONL format.
    
    Args:
        base_path: Path to the base directory containing event subdirectories
        output_dir: Optional output directory for combined files (defaults to base_path)
    """
    base_path = Path(base_path)
    
    if output_dir is None:
        output_dir = base_path
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Storage for combined data
    combined_data = {
        'dev': [],
        'test': [],
        'train': []
    }
    
    # Process each subdirectory
    for subdir in base_path.iterdir():
        if not subdir.is_dir():
            continue
            
        disaster_type = identify_disaster_type(subdir.name)
        print(f"Processing {subdir.name} as {disaster_type}...")
        
        # Look for TSV files
        for tsv_file in subdir.glob('*.tsv'):
            filename = tsv_file.stem.lower()
            
            # Determine file type
            if filename.endswith('_dev'):
                file_type = 'dev'
            elif filename.endswith('_test'):
                file_type = 'test'
            elif filename.endswith('_train'):
                file_type = 'train'
            else:
                continue  # Skip files that don't match our pattern
            
            print(f"  - Processing {tsv_file.name} ({file_type})...")
            
            # Convert TSV to list of dicts
            try:
                entries = tsv_to_jsonl(str(tsv_file), disaster_type)
                combined_data[file_type].extend(entries)
                print(f"    Added {len(entries)} entries")
            except Exception as e:
                print(f"    Error processing {tsv_file.name}: {e}")
    
    # Write combined JSONL files
    for file_type, entries in combined_data.items():
        if entries:
            output_path = output_dir / f"combined_{file_type}.jsonl"
            print(f"\nWriting {len(entries)} entries to {output_path}...")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')
    
    # Print summary
    print("\n=== Summary ===")
    print(f"Train entries: {len(combined_data['train'])}")
    print(f"Dev entries: {len(combined_data['dev'])}")
    print(f"Test entries: {len(combined_data['test'])}")
    print(f"\nOutput files saved to: {output_dir}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python script.py <path_to_directory> [output_directory]")
        print("\nExample: python script.py ./humaid_data")
        print("         python script.py ./humaid_data ./output")
        sys.exit(1)
    
    base_directory = sys.argv[1]
    output_directory = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(base_directory):
        print(f"Error: Directory '{base_directory}' does not exist")
        sys.exit(1)
    
    process_directory(base_directory, output_directory)