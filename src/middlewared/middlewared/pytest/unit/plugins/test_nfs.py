from mock import ANY, Mock, patch

from middlewared.plugins.nfs import SharingNFSService


def test__sharing_nfs_service__validate_paths__same_filesystem():
    with patch("middlewared.plugins.nfs.os.stat", lambda dev: {
        b"/mnt/data-1": Mock(st_dev=1),
        b"/mnt/data-1/a": Mock(st_dev=1),
        b"/mnt/data-1/b": Mock(st_dev=1),
    }[dev]):
        middleware = Mock()

        verrors = Mock()

        SharingNFSService(middleware).validate_paths(
            {
                "paths": ["/mnt/data-1/a", "/mnt/data-1/b"],
                "alldirs": False,
            },
            "sharingnfs_update",
            verrors,
        )

        assert not verrors.add.called


def test__sharing_nfs_service__validate_paths__not_same_filesystem():
    with patch("middlewared.plugins.nfs.os.stat", lambda dev: {
        b"/mnt/data-1": Mock(st_dev=1),
        b"/mnt/data-2": Mock(st_dev=2),
        b"/mnt/data-1/d": Mock(st_dev=1),
        b"/mnt/data-2/d": Mock(st_dev=2),
    }[dev]):
        middleware = Mock()

        verrors = Mock()

        SharingNFSService(middleware).validate_paths(
            {
                "paths": ["/mnt/data-1/d", "/mnt/data-2/d"],
                "alldirs": False,
            },
            "sharingnfs_update",
            verrors,
        )

        verrors.add.assert_called_once_with("sharingnfs_update.paths.1",
                                            "Paths for a NFS share must reside within the same filesystem")


def test__sharing_nfs_service__validate_paths__mountpoint_and_subdirectory():
    with patch("middlewared.plugins.nfs.os.stat", lambda dev: {
        b"/mnt": Mock(st_dev=0),
        b"/mnt/data-1": Mock(st_dev=1),
        b"/mnt/data-1/a": Mock(st_dev=1),
    }[dev]):
        middleware = Mock()

        verrors = Mock()

        SharingNFSService(middleware).validate_paths(
            {
                "paths": ["/mnt/data-1", "/mnt/data-1/a"],
                "alldirs": False,
            },
            "sharingnfs_update",
            verrors,
        )

        verrors.add.assert_called_once_with("sharingnfs_update.paths.0",
                                            "You cannot share a mount point and subdirectories all at once")


def test__sharing_nfs_service__validate_paths__alldirs_for_nonmountpoint():
    with patch("middlewared.plugins.nfs.os.stat", lambda dev: {
        b"/mnt": Mock(st_dev=0),
        b"/mnt/data-1": Mock(st_dev=1),
        b"/mnt/data-1/a": Mock(st_dev=1),
    }[dev]):
        middleware = Mock()

        verrors = Mock()

        SharingNFSService(middleware).validate_paths(
            {
                "paths": ["/mnt/data-1/a"],
                "alldirs": True,
            },
            "sharingnfs_update",
            verrors,
        )

        verrors.add.assert_called_once_with("sharingnfs_update.alldirs", ANY)


def test__sharing_nfs_service__validate_paths__alldirs_for_mountpoint():
    with patch("middlewared.plugins.nfs.os.stat", lambda dev: {
        b"/mnt": Mock(st_dev=0),
        b"/mnt/data-1": Mock(st_dev=1),
        b"/mnt/data-1/a": Mock(st_dev=1),
    }[dev]):
        middleware = Mock()

        verrors = Mock()

        SharingNFSService(middleware).validate_paths(
            {
                "paths": ["/mnt/data-1"],
                "alldirs": True,
            },
            "sharingnfs_update",
            verrors,
        )

        assert not verrors.add.called


def test__sharing_nfs_service__validate_user_networks__same_device_multiple_shares_alldir():
    with patch("middlewared.plugins.nfs.os.stat", lambda dev: {
        b"/mnt/data/a": Mock(st_dev=1),
        b"/mnt/data/b": Mock(st_dev=1),
    }[dev]):
        middleware = Mock()

        verrors = Mock()

        SharingNFSService(middleware).validate_user_networks(
            [
                {
                    "paths": ["/mnt/data/a"],
                    "networks": ["192.168.100.0/24"],
                    "alldirs": True,
                }
            ],
            {
                "paths": ["/mnt/data/b"],
                "networks": ["192.168.200.0/24"],
                "alldirs": True,
            },
            "sharingnfs_update",
            verrors,
        )

        verrors.add.assert_called_once_with("sharingnfs_update.alldirs", ANY)


def test__sharing_nfs_service__validate_user_networks__not_overlapping_networks():
    with patch("middlewared.plugins.nfs.os.stat", lambda dev: {
        b"/mnt/data/a": Mock(st_dev=1),
        b"/mnt/data/b": Mock(st_dev=1),
    }[dev]):
        middleware = Mock()

        verrors = Mock()

        SharingNFSService(middleware).validate_user_networks(
            [
                {
                    "paths": ["/mnt/data/a"],
                    "networks": ["192.168.100.0/24"],
                    "alldirs": False,
                }
            ],
            {
                "paths": ["/mnt/data/b"],
                "networks": ["192.168.101.0/25"],
                "alldirs": False,
            },
            "sharingnfs_update",
            verrors,
        )

        assert not verrors.add.called


def test__sharing_nfs_service__validate_user_networks__overlapping_networks():
    with patch("middlewared.plugins.nfs.os.stat", lambda dev: {
        b"/mnt/data/a": Mock(st_dev=1),
        b"/mnt/data/b": Mock(st_dev=1),
    }[dev]):
        middleware = Mock()

        verrors = Mock()

        SharingNFSService(middleware).validate_user_networks(
            [
                {
                    "paths": ["/mnt/data/a"],
                    "networks": ["192.168.100.0/24"],
                    "alldirs": False,
                }
            ],
            {
                "paths": ["/mnt/data/b"],
                "networks": ["192.168.100.0/25"],
                "alldirs": False,
            },
            "sharingnfs_update",
            verrors,
        )

        verrors.add.assert_called_once_with("sharingnfs_update.networks.0", ANY)
