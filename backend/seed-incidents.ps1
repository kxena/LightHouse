# Requires backend running at http://localhost:8000
$api = "http://localhost:8000"

Write-Host "Seeding dummy incidents via $api ..." -ForegroundColor Cyan

function Analyze-Tweet([hashtable]$tweet, [string]$incidentType, [string]$severity, [string]$location, [string[]]$entities) {
  $payload = @{ 
    tweet = $tweet
    is_disaster_related = $true
    incident_type = $incidentType
    severity = $severity
    location = $location
    key_entities = $entities
    confidence_score = 0.9
  } | ConvertTo-Json -Depth 8

  Invoke-RestMethod -Uri "$api/analyze-tweet" -Method POST -ContentType 'application/json' -Body $payload
}

function Add-Tweet-ToIncident([string]$incidentId, [hashtable]$tweet) {
  $body = $tweet | ConvertTo-Json -Depth 6
  Invoke-RestMethod -Uri "$api/incidents/$incidentId/add-tweet" -Method POST -ContentType 'application/json' -Body $body
}

# Incident 1: Power Outage (Austin)
$tweet1a = @{ text = "BREAKING: Major power outage in downtown Austin! Traffic lights down near 6th St. #PowerOutage #AustinTX"; author = "@AustinNewsNow"; timestamp = (Get-Date).ToUniversalTime().ToString("s") + "Z"; tweet_id = "PO-1"; engagement = @{ likes = 156; retweets = 89; replies = 34 } }
$r1 = Analyze-Tweet -tweet $tweet1a -incidentType "Power Outage" -severity "high" -location "Austin, Texas" -entities @("PowerOutage","Downtown","Austin")

if ($r1.incident_created) {
  $inc1 = $r1.incident_id
  Write-Host "Created Incident: $inc1" -ForegroundColor Green
  $tweet1b = @{ text = "Still no power downtown. Businesses closed and traffic is chaos. Any ETA? #AustinPowerOutage"; author = "@concerned_citizen"; timestamp = (Get-Date).AddMinutes(-15).ToUniversalTime().ToString("s") + "Z"; tweet_id = "PO-2"; engagement = @{ likes = 78; retweets = 45; replies = 23 } }
  $a1 = Add-Tweet-ToIncident -incidentId $inc1 -tweet $tweet1b
}

# Incident 2: Flash Flood (Shoal Creek)
$tweet2a = @{ text = "Flash flood warning! Water rising rapidly near Shoal Creek. Avoid low water crossings. #AustinFloods"; author = "@ATXWeatherAlert"; timestamp = (Get-Date).AddMinutes(-40).ToUniversalTime().ToString("s") + "Z"; tweet_id = "FF-1"; engagement = @{ likes = 245; retweets = 189; replies = 67 } }
$r2 = Analyze-Tweet -tweet $tweet2a -incidentType "Flash Flood" -severity "critical" -location "Austin, Texas - Shoal Creek Area" -entities @("FloodWarning","ShoalCreek","Austin")

if ($r2.incident_created) {
  $inc2 = $r2.incident_id
  Write-Host "Created Incident: $inc2" -ForegroundColor Green
  $tweet2b = @{ text = "Car swept away on Lamar near Shoal Creek! First responders on scene. Stay clear! #Emergency"; author = "@eyewitness_atx"; timestamp = (Get-Date).AddMinutes(-25).ToUniversalTime().ToString("s") + "Z"; tweet_id = "FF-2"; engagement = @{ likes = 312; retweets = 256; replies = 89 } }
  $a2 = Add-Tweet-ToIncident -incidentId $inc2 -tweet $tweet2b
}

# Output all incidents
$all = Invoke-RestMethod -Uri "$api/incidents" -Method GET
Write-Host ("Seed complete. Incidents: {0}" -f $all.Count) -ForegroundColor Cyan
$all | ForEach-Object { Write-Host (" - {0} {1} ({2} tweets)" -f $_.id, $_.incident_type, $_.source_tweets.Count) }