# Flights

Simple overview of use/purpose.

## Description

An in-depth paragraph about your project and overview of use.

## Getting Started

### Dependencies

* Describe any prerequisites, libraries, OS version, etc., needed before installing program.
* ex. Windows 10

### Installing

* How/where to download your program
* Any modifications needed to be made to files/folders

### Executing program

* How to run the program
* Step-by-step bullets
```
code blocks for commands
```
## To Do
data cleaning:
   - redo timezones(maybe)
   - get rid of airports without fligths(maybe)
   - add missing airports to the airports table
   - missing weather data: wind speed, wind direction
   - missing plane data: year
   - missing flights data: dep_time, dep_delay, arr_time, arr_delay, tailnum, airtime
   - missing airport data: tz, dst, tzone

Iwe:
   - improve wind direction vs airtime scatterplot
   - add airports
   - get rid of useless airports
   - setup data cleaning file

## Notes

- Missing airports: SJU, STT, BQN, PSE
    * SJU: 18.4333333 -66
    * STT: 18.3333333 -64.96666666666667
    * BQN: 18.495 -67.12944444444443
    * PSE: 18.0083333 -66.56305555555555
- A lot of airports have no flights going to them
- Some airports appear in the sea because the islands they're on are not shown on the map

## Help

Any advise for common problems or issues.
```
command to run if program contains helper info
```

## Authors

Contributors names and contact info

ex. Dominique Pizzie  
ex. [@DomPizzie](https://twitter.com/dompizzie)

## Version History

* 0.2
    * Various bug fixes and optimizations
    * See [commit change]() or See [release history]()
* 0.1
    * Initial Release

## License

This project is licensed under the [NAME HERE] License - see the LICENSE.md file for details

## Acknowledgments

Inspiration, code snippets, etc.
* [awesome-readme](https://github.com/matiassingers/awesome-readme)
* [PurpleBooth](https://gist.github.com/PurpleBooth/109311bb0361f32d87a2)
* [dbader](https://github.com/dbader/readme-template)
* [zenorocha](https://gist.github.com/zenorocha/4526327)
* [fvcproductions](https://gist.github.com/fvcproductions/1bfc2d4aecb01a834b46)
