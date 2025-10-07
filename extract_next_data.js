const fs = require('fs')

const htmlPath = process.argv[2] || 'mercari_page.html'
const outPath = process.argv[3] || 'mercari_data.json'

const html = fs.readFileSync(htmlPath, 'utf8')
const marker = '__NEXT_DATA__'
const markerIndex = html.indexOf(marker)

if (markerIndex === -1) {
  console.error('Unable to find __NEXT_DATA__ marker')
  process.exit(1)
}

const openTagStart = html.lastIndexOf('<script', markerIndex)

if (openTagStart === -1) {
  console.error('Unable to locate opening <script> tag')
  process.exit(1)
}

const openTagEnd = html.indexOf('>', markerIndex)

if (openTagEnd === -1) {
  console.error('Unable to locate end of <script> tag')
  process.exit(1)
}

const startContent = openTagEnd + 1
const end = html.indexOf('</script>', startContent)

if (end === -1) {
  console.error('Unable to find closing </script> tag for __NEXT_DATA__')
  process.exit(1)
}

const json = html.slice(startContent, end)
fs.writeFileSync(outPath, json)

console.log(`Extracted ${json.length} characters from ${htmlPath} to ${outPath}`)

