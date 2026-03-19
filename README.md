# Aperture

<img width="1948" height="1140" alt="image" src="https://github.com/user-attachments/assets/860d45eb-3b48-4c0c-bfbf-287f30492c77" />

## Introduction

The world needs instantly inclusive software that empowers blind and deaf users to participate equally in society. Many modern solutions, such as screen readers or subtitle generators, are reverse-engineered workarounds with frustrating accessibility gaps. These tools don’t function properly with every software, creating critical accessibility problems such as broken tab navigation or inaccurate text-to-speech readouts that ultimately confuse the user. Software should simply work for everyone out-of-the-box. So instead of patching problems in software, why not engineer an exemplary solution from the start?

Aperture is a software-augmenting tool that ensures blind and deaf people get equal access while using any software, automatically. Aperture is the first of its kind to give any desktop application/software native accessibility through automated code editing that implements important assistive features such as keyboard navigation and voice commands. Aperture works directly with a software’s code, rather than reverse engineering with screen readers or subtitles, and it’s simply a matter of copy-pasting a GitHub link. By leveraging a HuggingFace LLM (Qwen-Coder-30B), our software is able to edit entire codebases and make them accessible in minutes.

## Usage

Navigate to the "download" folder (https://github.com/nicfanst/Aperture/tree/master/download), then download the correct executable for your operating system. Make sure you have both a GitHub and HuggingFace account, since you will need to log in to both for Aperture's code editing features. Ensure that you have HuggingFace tokens available for use (HuggingFace provides limited access to some free tokens); Aperture will simply return to the home screen if you don't have any tokens, as the HuggingFace API will not be able to be accessed.

The zipped Setup Executable is ~1.2 GB. Be sure to have ~2 GB of free space on your disk for installation. The large size of the Aperture application is due in part to its self-contained nature; eliminating the need for installing external requirements requires us to package all dependencies within this single executable. Additionally, many AI models (e.g. Whisper for audio transcription) are installed locally to ensure that users of an Aperture-edited repository have full data safety with internal use of AI models. In the future, we will continue to optimize the software to reduce its working size.

## Software Design

The following is a flowchart reflecting Aperture's design.
<img width="1159" height="1072" alt="image" src="https://github.com/user-attachments/assets/bc3d1796-f449-45cd-b4d2-e15bce76f3fc" />

The Aperture Library is what implements each important accessibility feature. It is compiled into an executable for use in any other software repository. The Code Editing is the series of Python files responsible for editing (via HuggingFace) and releasing accessibility changes to a software repository. We use Electron for a user interface, so you can input a GitHub repository link to make accessible using Aperture.
