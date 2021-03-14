import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage

cred = credentials.Certificate('.auth/curation-system-firebase-adminsdk.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'curation-system.appspot.com'
})
bucket = storage.bucket()


def upload_blob(source_file_name, destination_blob_name):
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    return (
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )


def download_blob(source_blob_name, destination_file_name):
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)
    return (
        "Blob {} downloaded to {}.".format(
            source_blob_name, destination_file_name
        )
    )


def blob_list(prefix=""):
    blobs = list(bucket.list_blobs(prefix=prefix))
    return (
        "Blob list to {}.".format(
            blobs
        )
    )
