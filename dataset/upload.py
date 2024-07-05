from pathlib import Path
from huggingface_hub import HfApi

api = HfApi()


def _remove_uploaded(log: Path, filelist: list) -> list:
    '''
    remove uploaded files from filelist
    '''
    with log.open() as f:
        uploaded_list = f.readlines()
    for line in uploaded_list:
        filelist.remove(Path(line.strip()))
    return filelist


def _write_uploaded(log: Path, uploaded: Path) -> None:
    '''
    write uploaded file to log
    '''
    with log.open("a") as f:
        f.write(str(uploaded) + '\n')
    return


def _is_filtered(file: Path, filter: list[str]) -> bool:
    '''
    check if the file path need to be filtered
    '''
    for pattern in filter:
        if pattern in str(file):
            return True
    return False


def _walk_dir(datap: Path, filter: list[str]) -> list[Path]:
    '''
    walk through the directory
    '''
    filelist = []
    for file in datap.glob('*'):
        if _is_filtered(file, filter):
            continue

        if file.is_dir():
            filelist = filelist + _walk_dir(file, filter)
        else:
            filelist.append(file)

    return filelist


def _loadfiles(datap: Path, filter: list[str], log: Path) -> list[Path]:
    '''
    load all the files to upload
    '''
    filelist = _walk_dir(datap, filter)
    filelist = _remove_uploaded(log, filelist)
    return filelist


def upload_dataset(dataset_dir: str) -> None:
    '''
    main function to upload dataset
    '''
    datap = Path(dataset_dir)
    log = datap / 'uploaded'
    if not log.exists():
        log.touch()

    filelist = _loadfiles(datap, ['.git', 'ManualPick', 'uploaded'], log)

    for file in filelist:
        api.upload_file(
            path_or_fileobj=str(file),
            path_in_repo=str(file.relative_to(datap)),
            repo_id='Aaaapril/PS_Alaska',
            repo_type='dataset',
        )
        _write_uploaded(log, file)
    return

upload_dataset('/mnt/scratch/jieyaqi/alaska/final/PS_Alaska')
    

# Upload dataset to huggingface


