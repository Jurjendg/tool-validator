param(
  [Parameter(Mandatory = $true)]
  [string]$Xml,

  [Parameter(Mandatory = $true)]
  [string]$Out,

  [string]$Xsd
)

if ($Xsd) {
  xml-converter extract --xml $Xml --out $Out --xsd $Xsd
} else {
  xml-converter extract --xml $Xml --out $Out
}
