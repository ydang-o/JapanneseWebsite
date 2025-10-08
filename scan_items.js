const fs = require('fs')

const data = JSON.parse(fs.readFileSync(process.argv[2] || 'mercari_data.json', 'utf8'))

function findItems(obj, path = []) {
  if (Array.isArray(obj)) {
    if (
      obj.length &&
      typeof obj[0] === 'object' &&
      obj[0] !== null &&
      ('name' in obj[0] || 'title' in obj[0]) &&
      ('price' in obj[0] || 'prices' in obj[0] || 'amount' in obj[0])
    ) {
      console.log('Possible product array at', path.join('.'))
      console.log(JSON.stringify(obj.slice(0, 3), null, 2))
      console.log('---')
    }
    obj.forEach((value, index) => findItems(value, path.concat(index)))
    return
  }

  if (obj && typeof obj === 'object') {
    for (const [key, value] of Object.entries(obj)) {
      if (key === 'items' && Array.isArray(value)) {
        console.log('Found items array at', path.concat(key).join('.'))
        console.log(JSON.stringify(value.slice(0, 3), null, 2))
        console.log('---')
      }
      findItems(value, path.concat(key))
    }
  }
}

findItems(data)

