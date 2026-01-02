function parseRideQuerySimple(query) {
    const queryLower = query.toLowerCase();
    let origin = null;
    let destination = 'Times Square, NYC';

    // Remove common filler words that appear before "to"
    let cleaned = queryLower;
    cleaned = cleaned.replace(/\b(need|want|like)\s+(to|a)\s+(take|get|book|find|have)\s+(a|an|the)?\s*(ride|uber|lyft|taxi|cab)\s+to\s+/gi, 'to ');
    cleaned = cleaned.replace(/\b(need|want|like)\s+to\s+(go|head|travel)\s+to\s+/gi, 'to ');

    // Now extract destination after "to"
    const toMatch = cleaned.match(/\bto\s+([a-z][a-z\s,]+?)(?:\s*$|\.)/i);
    if (toMatch) {
        let dest = toMatch[1].trim();

        // Capitalize each word
        dest = dest.split(' ').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');

        // Add ", NYC" if not present
        if (!dest.includes(',') && !dest.toLowerCase().includes('nyc') && !dest.toLowerCase().includes('new york')) {
            dest = `${dest}, NYC`;
        }

        destination = dest;
    }

    // Try to extract origin - look for "from" pattern
    const fromMatch = queryLower.match(/\bfrom\s+([a-z\s,]+?)\s+to\s+/i);
    if (fromMatch) {
        let orig = fromMatch[1].trim();
        orig = orig.split(' ').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
        if (!orig.includes(',')) {
            orig = `${orig}, NYC`;
        }
        origin = orig;
    }

    return { origin, destination };
}

// Test cases
const testCases = [
    "need to take ride to times square",
    "need a ride to times square",
    "uber to JFK airport",
    "need to go to central park",
    "ride from brooklyn to manhattan",
    "taxi to LaGuardia"
];

console.log("Testing ride query parsing:\n");
testCases.forEach(query => {
    const result = parseRideQuerySimple(query);
    console.log(`Query: "${query}"`);
    console.log(`  Origin: ${result.origin || 'null (use geolocation)'}`);
    console.log(`  Destination: ${result.destination}\n`);
});
