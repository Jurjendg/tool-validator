param(
  [Parameter(Mandatory = $true)]
  [string]$XmlDir,

  [Parameter(Mandatory = $true)]
  [string]$Out,

  [string]$Pattern = '*.xml'
)

xml-converter validate --xml-dir $XmlDir --out $Out --pattern $Pattern
