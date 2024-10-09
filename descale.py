import re
import subprocess
import os
import sys
import shutil

def read_assets(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def get_suffix(scale):
    return f'_s{str(scale).replace(".", "_")}'

def create_scaled_qc(mdl_path, scale, assets):
    suffix = get_suffix(scale)
    directory, filename = os.path.split(mdl_path)
    qc_name = filename.replace('.mdl', '.qc')
    new_qc_name = filename.replace('.mdl', f'{suffix}.qc')

    for asset_dir in assets:
        subprocess.run([
            'CrowbarCommandLineDecomp.exe',
            '-p', os.path.join(asset_dir, mdl_path),
            '-o', './original_qcs/'
        ])

    with open(os.path.join('./original_qcs', qc_name), 'r') as qc:
        content = [f'$scale {scale}\n']
        for line in qc:
            if '$bbox' in line:
                line = f'// {line}'
            elif '$modelname' in line:
                line = line.replace('.mdl', f'{suffix}.mdl')
            content.append(line)

    output_dir = os.path.join('./scaled_qcs', directory)
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, new_qc_name), 'w') as new_qc:
        new_qc.writelines(content)

def process_vmf(vmf_path, assets):
    output_path = vmf_path.replace('.vmf', '_descaled.vmf')

    model = None
    model_line = None

    with open(vmf_path, 'r') as f:
        lines = f.readlines()

        for cur_line, line in enumerate(lines):
            model_match = re.match(r'\s*"model"\s*"(.+)"', line)
            if model_match:
                model = model_match.group(1)
                model_line = cur_line

            scale_match = re.match(r'\s*"uniformscale"\s*"([^1].*)"', line)
            if scale_match:
                scale = scale_match.group(1)

                create_scaled_qc(model, scale, assets)

                suffix = get_suffix(scale)
                lines[model_line] = lines[model_line].replace('.mdl', f'{suffix}.mdl')
                lines[cur_line] = '\t"uniformscale" "1"\n'

    with open(output_path, 'w') as f:
        f.writelines(lines)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    assets_file_path = 'assets.txt'
    assets = read_assets(assets_file_path)

    if not assets:
        raise ValueError("No asset directories found in assets.txt")

    vmf_path = sys.argv[1]
    process_vmf(vmf_path, assets)
    shutil.rmtree('./original_qcs')
