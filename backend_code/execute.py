import sys
import subprocess

def run_script(script):
    
    print(f"Starting: {script}")
    
    try:
        
        result = subprocess.run(
            [sys.executable, script], 
            check=True, 
            text=True
        )
        
    except subprocess.CalledProcessError as e:
        print(f"\n Error running : {script}")
        sys.exit(1) 

if __name__ == "__main__":
    
    run_script("main.py")
    
    run_script("metrics_gen.py")
    
    run_script("visualizations.py")

