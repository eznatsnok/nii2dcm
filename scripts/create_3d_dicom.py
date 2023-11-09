"""
Create 3D Fetal Brain MRI SVRTK single-frame DICOM dataset NIfTI file

Tested with data from the following scanners:
- 1.5T Philips Ingenia
- 1.5T Siemens Sola
"""
import os
import nibabel as nib
import pydicom
from tqdm import tqdm
import nii2dcm.dcm_writer
import nii2dcm.nii
import nii2dcm.svr



NII2DCM_DIR = r'/data/home/hik37564/g_laufwerk/BA/nii2dcm'
INPUT_DIR = r'/data/home/hik37564/disk/lfb_net/files_nifti_format_3D_4x4x4_128x256/pet'
OUTPUT_DIR = r'/data/home/hik37564/disk/lfb_net/files_dcm_format_4x4x4_128x256/pet'


# Initialise
# TestDicomMRISVR = nii2dcm.svr.DicomMRISVR('0af7ffe12a.dcm')
DummyDicomPETDataset = pydicom.read_file("/data/home/hik37564/disk/lfb_net/files_dcm_format/PET/0af7ffe12a/1-001.dcm")
DummyDicomGTDataset = pydicom.read_file("/data/home/hik37564/disk/lfb_net/files_dcm_format/GT/0af7ffe12a/1-1.dcm")

for file in tqdm(os.listdir(INPUT_DIR)):
    # Load Nifti file
    niiInPath = os.path.join(INPUT_DIR, file)
    nii = nib.load(niiInPath)

    # Set output directory
    dcmOutPath = os.path.join(OUTPUT_DIR, file.split(".")[0])
    if not os.path.exists(dcmOutPath):
        os.makedirs(dcmOutPath)
        
    # Get NIfTI parameters to transfer to DICOM
    nii2dcm_parameters = nii2dcm.nii.Nifti.get_nii2dcm_parameters(nii)


    # Write single DICOM

    # Transfer Series tags
    nii2dcm.dcm_writer.transfer_nii_hdr_series_tags(DummyDicomPETDataset, nii2dcm_parameters)

    # Get NIfTI pixel data
    # TODO: create method in Nifti class – need to think about -1 value treatment
    nii_img = nii.get_fdata()
    nii_img[nii_img < 0] = 0  # set background pixels = 0 (negative in SVRTK)
    nii_img = nii_img.astype("uint16")  # match DICOM datatype

    # Set custom tags
    # - currently none

    # Write DICOM Series, instance-by-instance
    for instance_index in range(0, nii2dcm_parameters['NumberOfInstances']):

        # Transfer Instance tags
        nii2dcm.dcm_writer.transfer_nii_hdr_instance_tags(DummyDicomPETDataset, nii2dcm_parameters, instance_index)

        # Write slice
        dcm, img_data, instance_index, output_dir = DummyDicomPETDataset, nii_img, instance_index, dcmOutPath
        output_filename = r'IM_%04d.dcm' % (instance_index + 1)  # begin filename from 1, e.g. IM_0001.dcm

        img_slice = img_data[:,:,instance_index ]

        # Instance UID – unique to current slice
        dcm.SOPInstanceUID = pydicom.uid.generate_uid(None)

        # write pixel data
        dcm.PixelData = img_slice.tobytes() # adds pixeldata tag and pixelarray tag
        dcm.LargestImagePixelValue = img_slice.max()  # heult ohne den wert rum
        # dcm.InstanceNumber = instance_index + 1  # begin from 1, not 0
        # dcm.SliceThickness = nii.header['pixdim'][3] 
        # dcm.PixelSpacing = nii.header['pixdim'][1:2]


        # write DICOM file
        dcm.save_as(os.path.join(output_dir, output_filename), write_like_original=False)
        #nii2dcm.dcm_writer.write_slice(TestDicomMRISVR, nii_img, instance_index, dcmOutPath)

