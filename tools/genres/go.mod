module genres

go 1.24.0

require github.com/tc-hib/winres v0.0.0

require (
	github.com/nfnt/resize v0.0.0 // indirect
	golang.org/x/image v0.33.0 // indirect
)

replace (
	github.com/nfnt/resize => ./third_party/resize
	github.com/tc-hib/winres => ./third_party/winres
	golang.org/x/image => ./third_party/image
)
