# Aperture

Aperture is a software-augmenting tool that ensures blind and deaf people get equal access while using any software, automatically. Aperture is the first of its kind to give any desktop application/software native accessibility through automated code editing that implements important assistive features such as keyboard navigation and voice commands. Aperture works directly with a software’s code, rather than reverse engineering with screen readers or subtitles, and it’s simply a matter of copy-pasting a GitHub link. By making API calls to a HuggingFace LLM (Qwen-Coder-30B), our software is able to edit entire codebases and make them accessible in minutes.

## Usage

Navigate to the "download" folder (https://github.com/nicfanst/Aperture/tree/master/download), then download the correct executable for your operating system.

## Software Design

The following is a flowchart reflecting Aperture's design.
<img width="1105" height="1110" alt="Screenshot 2026-03-18 190538" src="https://github.com/user-attachments/assets/b6d0be9e-a0e4-4190-8c2a-f7496502c459" />

The Aperture Library is what implements each important accessibility feature. It is compiled into an executable for use in any other software repository. The Code Editing is the series of Python files responsible for editing (via HuggingFace) and releasing accessibility changes to a software repository. We use Electron for a user interface, so you can input a GitHub repository link to make accessible using Aperture.
