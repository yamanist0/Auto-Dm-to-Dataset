<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![Unlicense License][license-shield]][license-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <h3 align="center">Auto DM to Dataset</h3>

  <p align="center">
    A powerful CLI tool to convert your chat histories into AI training datasets!
    <br />
    <a href="#usage"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/yamanist0/dm-to-dataset/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/yamanist0/dm-to-dataset/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About The Project

[![Product Name Screen Shot][product-screenshot]](screenshot.png)

Auto DM to Dataset: An interactive CLI tool which converts your personal chat exports (from different Social Platforms such as Whatsapp, Instagram etc. Etc.) into a well formatted JSONL file which you can directly use to fine-tune LLMs on your writing style, tones, tone of the relationship etc etc.

Currently supported platforms:
* **Instagram** (JSON inbox format)
* **WhatsApp** (TXT chat export format)
* **TikTok** (JSON user data format)

### Key Features
* **Interactive TUI**: Simple terminal user interface that allows configuration of and running of the tool using keys up/down/left/right without the need of learning specific commands.
* **Custom Categories**: Map all your chats to relationship types (“friend”, “ flirt”, etc) and custom system prompt (all your chats).
* **Role Assignment**: Choose your custom names for the script to properly recognize the display names in `user` & `assistant` messages.
* **Privacy Focused**: Filter by Username or Chat You would not like to include in your list of data to be analyzed.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

The tool uses only the standard Python libraries to ensure maximal portability, nothing outside the base installation of Python.
* [![Python][Python.org]][Python-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started

Follow below the simplest guidelines as listed below for having your local copy running:

### Prerequisites

You need to have Python installed on your system.
* Python 3.8+

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/yamanist0/dm-to-dataset.git
   ```
2. Navigate to the directory
   ```sh
   cd dm-to-dataset
   ```
3. Run the interactive CLI
   ```sh
   python main.py
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->
## Usage

Running `python main.py` without arguments will launch the interactive menu where you can:
1. **Set Assistant Names**: Fill in the names / aliases you use in chats. This tells the tool to label your messages to us as `assistant`.
2. **Add Categories**: Set up categories with a prompt on how to respond, like `friend` category and then the prompt `relationship type: friend. Use a casual and funny tone`.
3. **Add Chat Paths**: Specify the directory where your chat export from instagram, whatsapp or tiktok is saved.
4. **Process Data**: Combine all chats, use system prompts to write conversation turns and save to file like below, for example `output.jsonl`
```json
{
    "messages": [
        {
            "role": "user",
            "content": "Hey, how are you?"
        },
        {
            "role": "assistant",
            "content": "I'm fine, thanks!"
        }
    ]
}
```

Alternatively, you can use standard CLI arguments:
```bash
python main.py config --show
python main.py config --add-category "friend" "act like a friend"
python main.py config --add-ig-path "C:\path\to\instagram\messages"
python main.py run
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ROADMAP -->
## Roadmap

- [x] Support Instagram JSON data
- [x] Support WhatsApp TXT data
- [x] Support TikTok JSON data
- [x] Interactive CLI Menu
- [ ] Add Telegram support
- [ ] Token count estimation

See the [open issues](https://github.com/yamanist0/dm-to-dataset/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->
## License

Distributed under the Unlicense License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
[contributors-shield]: https://img.shields.io/github/contributors/yamanist0/dm-to-dataset.svg?style=for-the-badge
[contributors-url]: https://github.com/yamanist0/dm-to-dataset/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/yamanist0/dm-to-dataset.svg?style=for-the-badge
[forks-url]: https://github.com/yamanist0/dm-to-dataset/network/members
[stars-shield]: https://img.shields.io/github/stars/yamanist0/dm-to-dataset.svg?style=for-the-badge
[stars-url]: https://github.com/yamanist0/dm-to-dataset/stargazers
[issues-shield]: https://img.shields.io/github/issues/yamanist0/dm-to-dataset.svg?style=for-the-badge
[issues-url]: https://github.com/yamanist0/dm-to-dataset/issues
[license-shield]: https://img.shields.io/github/license/yamanist0/dm-to-dataset.svg?style=for-the-badge
[license-url]: https://choosealicense.com/licenses/unlicense/
[product-screenshot]: screenshot.png
[Python.org]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/

"# Auto-Dm-to-Dataset" 
