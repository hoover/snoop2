"""Tasks to decrypt gpg email and import keys.

Requires the passphrase be removed from the key and imported into the "gpghome" directory under the
collection dataset root.
"""
import subprocess

from .. import collections
from ..tasks import SnoopTaskBroken


def is_encrypted(data):
    """Checks if string data encodes PGP encrypted message.

    Only works in the text representation (that begins with `-----BEGIN PGP MESSAGE-----`.
    any binary encodings will not work.
    """

    return b'-----BEGIN PGP MESSAGE-----' in data


def decrypt(data):
    """Runs `gpg --decrypt` on the given data with the given collection `gpghome` dir."""

    gpghome = collections.current().gpghome_path
    if not gpghome.exists():
        raise SnoopTaskBroken("No gpghome folder", 'gpg_not_configured')

    result = subprocess.run(
        ['gpg', '--home', gpghome, '--decrypt'],
        input=data,
        check=True,
        stdout=subprocess.PIPE,
    )
    return result.stdout


def import_keys(keydata):
    """Runs `gpg --import` on the given key data, to be saved in the collection `gpghome`.

    This requires that the keydata be with passphrase removed.

    Arguments:
        keydata: data supplied to `gpg` process stdin
    """
    gpghome = collections.current().gpghome_path
    subprocess.run(
        ['gpg', '--home', gpghome, '--import'],
        input=keydata,
        check=True,
    )
