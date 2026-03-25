"""All Configureables should go here

Returns:
    None
"""
from utils import get_full_path


class Printable:
    def _get_attributes(self):
        attributes = [
            attr
            for attr in dir(self)
            if not attr.startswith("__") and not callable(getattr(self, attr))
        ]

        return attributes

    def _get_dict(self):
        attributes = self._get_attributes()
        d = {i: getattr(self, i) for i in attributes}
        return d

    def __repr__(self):
        d = self._get_dict()
        s = str(d)
        return s

    def __iter__(self):
        for k, v in self._get_dict().items():
            yield k, v


class Config(Printable):
    DB = "centrox"
    COLLECTION = "cloths"
    AWS_ACCESS_KEY_ID = ""
    AWS_SECRET_ACCESS_KEY = ""
    INDEX_BUCKET = "imagesearch-indexes"
    MONGO_HOST = ""
    MONGO_USERNAME = ""
    MONGO_PASSWORD = ""
    MONGO_AUTHSOURCE = "centrox"
    MONGO_DATABASE = "centrox"
    REDIS_HOST = ""
    REDIS_PASSWORD = ""
    REDIS_PORT = "6379"
    AI_URL = ""
    CLOTH_COUNT_URI = ""
    GENDER_HOST = ""
    IMAGE_RETRIEVAL_HOST = ""
    IMAGE_RETRIEVAL_MODELNAME = "resnet_encoder_inter"
    IMAGE_RETRIEVAL_VERSION = 1
    IMAGE_SIZE = 128
    EMBEDDING_SIZE = 128
    CLOSEST_TOP_K = 10
    BATCH_SIZE = 50
    INDEX_DIR = get_full_path("../data")
