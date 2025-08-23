import hashlib

def hash_content(content):
    return hashlib.md5(content.encode()).hexdigest()

def create_block(data, previous_hash=''):
    block_str = str(sorted(data.items())) + previous_hash
    return {
        'data': data,
        'previous_hash': previous_hash,
        'hash': hash_content(block_str)
    }
