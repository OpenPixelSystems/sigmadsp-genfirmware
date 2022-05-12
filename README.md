# sigmadsp-genfirmware

## SigmaDSP Firmware Utility for Linux

The SigmaDSP Firmware Utility for Linux allows to generate a firmware file which can be loaded by the Linux SigmaDSP device drivers.

## Usage

Generating a binary can be done as follows:

```sh
$ sigmadsp_fwgen <path_to_xml_file> <samplerate> <output_file>
```

This file should then be stored in /lib/firmware or /var/lib/firmware so that a ALSA codec driver can find and program the DSP firmware via the SigmaDSP layer.
