from string import Template

def generate_yaml(num):
    with open('scripts_phasenet/alaska_tonga.yaml', 'r') as f:
        tem = f.readlines()

    t = Template(';'.join(tem))
    new_text = t.substitute(num=num)
    with open(f'/mnt/home/jieyaqi/code/PhaseNet-TF/configs/experiment/alaska_tonga{num}.yaml', 'w') as f:
        f.writelines(new_text.split(';'))
    return 

if __name__ == '__main__':
    for i in range(1, 7):
        generate_yaml(i)