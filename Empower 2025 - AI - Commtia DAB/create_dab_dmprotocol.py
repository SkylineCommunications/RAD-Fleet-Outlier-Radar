import argparse
import pathlib
import shutil
import tempfile
import subprocess
import sys

# Ensure pandas is installed
try:
    import pandas as pd
except ImportError:
    print("pandas not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
    import pandas as pd

def replace_placeholders(protocol_dir, output_dir, protocol_version_suffix, data):
    for input_path in pathlib.Path(protocol_dir).glob('**/*'):
        if not input_path.is_file():
            continue
        
        with open(input_path, 'r') as f:
            content = f.read()
            content = content.replace('{PROTOCOL_VERSION_SUFFIX}', protocol_version_suffix)
            content = content.replace('//PROTOCOL_DATA_PA1', ',\n'.join(data['pa1'].values.astype(str)))
            content = content.replace('//PROTOCOL_DATA_PA2', ',\n'.join(data['pa2'].values.astype(str)))
            content = content.replace('//PROTOCOL_DATA_PA3', ',\n'.join(data['pa3'].values.astype(str)))
            content = content.replace('//PROTOCOL_DATA_TOTAL_OUTPUT_POWER', ',\n'.join(data['total_output_power'].values.astype(str)))

        
        relative_path = input_path.relative_to(protocol_dir)
        output_path = pathlib.Path(output_dir) / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(content)

def create_dmprotocol_package(protocol_dir, output_dir, package_name):
    print(f'Creating {package_name}.dmprotocol in {output_dir}')
    output_file = output_dir / f'{package_name}'
    shutil.make_archive(str(output_file), 'zip', protocol_dir)
    shutil.move(f'{output_file}.zip', f'{output_file}.dmprotocol')

argparser = argparse.ArgumentParser(description='Create .dmprotocol files from directories with protocols')
argparser.add_argument('protocols', nargs='*', help='Directories with protocols')
argparser.add_argument('--output-dir', help='Output directory for .dmprotocol files')
argparser.add_argument('--package-name', help='Name of the package (can only be used with one protocol)')
argparser.add_argument('--data-dir', help='Directory with all csv data')
args = argparser.parse_args()

if args.output_dir is None:
    raise ValueError('Output directory argument is required')
if len(args.protocols) == 0:
    raise ValueError('At least one protocol directory must be specified')
if len(args.protocols) > 1 and args.package_name is not None:
    raise ValueError('Package name argument can only be used with one protocol')

output_dir = pathlib.Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)
for protocol in args.protocols:
    if args.package_name is not None:
        package_name = args.package_name
    else:
        package_name = pathlib.Path(protocol).name

    for data_file in pathlib.Path(args.data_dir).glob('*.csv'):
        data = pd.read_csv(data_file)

        temp_dir = tempfile.mkdtemp()
        replace_placeholders(
            protocol_dir=protocol,
            output_dir=temp_dir,
            protocol_version_suffix=data_file.stem,
            data=data
        )
        create_dmprotocol_package(
            protocol_dir=temp_dir,
            output_dir=output_dir,
            package_name=f'{package_name}_{data_file.stem}'
        )
        shutil.rmtree(temp_dir)