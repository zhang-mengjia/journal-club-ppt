param(
    [Parameter(Mandatory = $true)][string]$PresentationPath,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [int]$Width = 1280,
    [int]$Height = 720
)

$ErrorActionPreference = 'Stop'
$resolvedPresentation = (Resolve-Path -LiteralPath $PresentationPath).Path
$renderDirectory = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $renderDirectory -Force | Out-Null
$powerPoint = $null
$presentation = $null
try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    $presentation = $powerPoint.Presentations.Open($resolvedPresentation, $true, $false, $false)
    foreach ($slide in $presentation.Slides) {
        $filename = 'slide-{0:D3}.png' -f $slide.SlideIndex
        $slide.Export((Join-Path -Path $renderDirectory -ChildPath $filename), 'PNG', $Width, $Height)
    }
    Write-Output ('Rendered slides ' + $presentation.Slides.Count)
}
finally {
    if ($null -ne $presentation) {
        $presentation.Close()
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($presentation)
    }
    if ($null -ne $powerPoint) {
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($powerPoint)
    }
}
