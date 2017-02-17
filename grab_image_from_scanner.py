#! /usr/bin/env python
"""Retrieve an image from a specific series in the current exam."""
from __future__ import print_function
import sys
import argparse
from dcmstack import DicomStack

# Change this path to point to where the rtfmri code lives
sys.path.insert(0, "/home/cniuser/git/rtfmri")
from rtfmri import ScannerClient


def main(arglist):

    args = parse_args(arglist)
    client = ScannerClient(username=args.username, password=args.password)
    chosen_series = choose_series(client)
    build_nifti(client, chosen_series, args.outfile)


def parse_args(arglist):
    """Parse command line arguments."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("-username", required=True,
                   help="Username for scanner ftp server")
    p.add_argument("-password", required=True,
                   help="Password for scanner ftp server")
    p.add_argument("-outfile", required=True,
                   help="Filename for image to create")
    return p.parse_args(arglist)


def choose_series(client):
    """Allow user to select target series from existing series dirs."""
    series_dirs = client.series_dirs()
    series_info = {}

    # Report the description tag for each existing series in current exam
    print("Existing DICOM image series from current exam:")
    for i, series in enumerate(series_dirs, 1):
        info = client.series_info(series)
        series_info[series] = info
        description = info["Description"]
        if description != "Screen Save":
            print(" {:d}: {}".format(i, description))

    # Allow the user to select one of these series
    chosen_index = raw_input("Which series number? ")
    chosen_series = series_dirs[int(chosen_index) - 1]
    chosen_description = series_info[chosen_series]["Description"]
    print("Retrieving DICOM data for '{}'".format(chosen_description))
    return chosen_series


def build_nifti(client, series, nii_fname):
    """Pull DICOM data from the scanner and build a Nifti image with it."""
    src_paths = client.series_files(series)
    stack = DicomStack()

    # Retrieve the binary dicom data from the FTP server
    for path in src_paths:
        dcm = client.retrieve_dicom(path)
        stack.add_dcm(dcm)

    # Create a nibabel nifti object
    nii_img = stack.to_nifti(voxel_order="")

    # Write the nifti to disk
    print("Writing to {}".format(nii_fname))
    nii_img.to_filename(nii_fname)


if __name__ == "__main__":
    main(sys.argv[1:])
