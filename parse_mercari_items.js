const fs = require('fs')

const inputPath = process.argv[2] || 'mercari_page.html'
const outputPath = process.argv[3] || 'mercari_items.json'

const html = fs.readFileSync(inputPath, 'utf8')

const itemRegex = /<div id="(m\d+)" data-itemprice="(\d+)" data-itemstatus="([^"]+)"[^>]*>([\s\S]*?)<\/div><\/div><\/a><\/div>/g

const items = []

let match
while ((match = itemRegex.exec(html)) !== null) {
  const [, id, priceRaw, status, inner] = match

  const hrefMatch = inner.match(/href="([^"]+)"/)

  const imgMatch = inner.match(/<img[^>]*alt="([^"]*)"[^>]*title="([^"]*)"[^>]*srcset="([^"]*)"[^>]*src="([^"]*)"[^>]*>/)

  const priceTextMatch = inner.match(/data-testid="ItemPrice"[^>]*>([^<]+)/)

  const discountMatch = inner.match(/data-testid="ItemDecorationRectangle"[\s\S]*?<p[^>]*>([^<]+)<\/p>/)

  const item = {
    id,
    status,
    priceCents: Number(priceRaw),
    price: Number(priceRaw) / 100,
    priceText: priceTextMatch ? priceTextMatch[1] : null,
    href: hrefMatch ? hrefMatch[1] : null,
    image: imgMatch
      ? {
          alt: imgMatch[1],
          title: imgMatch[2],
          srcset: imgMatch[3],
          src: imgMatch[4],
        }
      : null,
    discount: discountMatch ? discountMatch[1] : null,
  }

  items.push(item)
}

fs.writeFileSync(outputPath, JSON.stringify(items, null, 2))

console.log(`Extracted ${items.length} items -> ${outputPath}`)

