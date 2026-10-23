"""Seed blog posts and fragments from the original React site content."""

from django.core.management.base import BaseCommand

from sitepages.models import BlogPost, Fragment

FRAGMENTS = [
    {
        "id": 4,
        "image": "dust-combination-everything-exist-olife-fragment4.png",
        "title": "The Dust of Existence",
        "alt_text": "Olife fragment - The dust is a combination of everything that exists",
        "sort_order": 4,
    },
    {
        "id": 3,
        "image": "no-witness-dark-side-olife-fragments3.png",
        "title": "No Witness Dark Side",
        "alt_text": "Olife fragment - no witness dark side",
        "sort_order": 3,
    },
    {
        "id": 2,
        "image": "light-and-dark-duality-olife-fragments2.png",
        "title": "Light and Dark Duality",
        "alt_text": "Olife fragment - light and dark duality",
        "sort_order": 2,
    },
    {
        "id": 1,
        "image": "DONTEVERFORGETfragments1.png",
        "title": "Don't Ever Forget",
        "alt_text": "Olife fragment - don't ever forget",
        "sort_order": 1,
    },
]

POSTS = [
    {
        "id": 3,
        "title": "What If the Sky is a Vault?",
        "episode": "S1E2",
        "excerpt": (
            "Science says reaching the edge of the universe takes millions of years. "
            "But what if the 'sky' described in Genesis requires a different kind of technology to cross?"
        ),
        "date_display": "29 March 2026",
        "image": "Olife1.comBlogpostsarticles3s1e2.png",
        "seo_title": "What If the Sky is a Vault?: Crossing the Horizontal Divide | Olife",
        "seo_description": (
            "Science says reaching the edge of the universe takes millions of years. "
            "But what if the 'sky' described in Genesis requires a different kind of technology to cross?"
        ),
        "seo_keywords": (
            "Genesis Vault, Waters Above, Human Consciousness, Space Travel Science, "
            "Olife, The Horizontal Divide, Inner Technology"
        ),
        "sort_order": 3,
        "content_html": """
<p>What if the story of creation holds a literal Blueprint for the structure of our reality?</p>
<h2>The Ancient Blueprint</h2>
<p>In the beginning, the text says: “Let there be a vault between the waters to separate water from water.” So God made the vault and separated the water under the vault from the water above it. And it was so. God called the vault “sky.”</p>
<p>If we look at this closely, a fascinating picture emerges. The Only One commanded a precise separation, and The Hand built a definitive boundary: the Horizontal Divide. According to this, the "waters above" are still up there. Everything we know, see, and experience as our physical universe was built underneath this ceiling. We live entirely within the waters below the sky.</p>
<p class="highlight">So, what if the Kingdom, the ultimate realm of Serenity, still exists right now in those waters above?</p>
<h2>The Scientific Barrier</h2>
<p>If the waters above are real, can we go there? When we look up, we see the vast expanse of space. Modern science confirms just how trapped we are by physical distance. Light travels at roughly 186,000 miles per second. Even at that unimaginable speed, it would take us over four years just to reach the nearest star, Proxima Centauri.</p>
<p>To cross our own Milky Way galaxy would take 100,000 years. To reach the edge of the observable universe—what we might call the limits of the vault—would take billions of light-years. Science tells us that under the current laws of physics (what we in Olife call the rules of the Big Noise), building a machine to take us to the very edge is impossible. Our metal ships and rocket fuel are bound by time and gravity. If we have to physically cross the sky to reach the waters above, we are stuck.</p>
<h2>What If We Are the Technology?</h2>
<p>But what if we are looking at the problem the wrong way? What if the greatest technology ever created isn't a machine, but us? What if the human mind and spirit are the exact tools needed to breach the vault? We spend billions trying to build ships that can survive the physical universe, but we are already equipped with a profound internal technology. As reflections of the Only One, we carry a unique Resonance within us.</p>
<p>What if we don't need to cross the sky in a spaceship? What if we can reach the waters above simply through our will, our consciousness, and who we are at our core? Instead of traveling through the physical distances of the Big Noise, what if we can tune our internal frequency to match the Harmony of the waters above, bridging the gap instantly?</p>
<p class="italic">Perhaps the vault was never meant to be crossed by machines. It was meant to be transcended by us.</p>
<div class="continued"><p>To be continued …</p></div>
""",
    },
    {
        "id": 2,
        "title": "The Infinite Waters",
        "episode": "S1E1",
        "excerpt": (
            "Discover the monumental horizontal division of the infinite waters and the creation "
            "of the mirrored universe, a divine gift for The Hand..."
        ),
        "date_display": "19 March 2026",
        "image": "Olife1.comBlogposts1e2.png",
        "seo_title": "The Infinite Waters S1E1: The Great Divide and the Mirrored Universe | Olife",
        "seo_description": (
            "Read about the horizontal division of the infinite waters, the creation of the mirrored "
            "universe, and the grand design intended as the ultimate prize for The Hand."
        ),
        "seo_keywords": (
            "Infinite waters, The Hand, mirrored universe, Only One, spiritual fiction, "
            "creation story, Olife Chronicles"
        ),
        "sort_order": 2,
        "content_html": """
<p>Once upon a time, within the grand design of the Only One, there existed the infinite waters. This boundless ocean of existence stretched endlessly, containing the potential for all things.</p>
<h2>The Horizontal Divide</h2>
<p>By the supreme will of the Only One, the infinite water was separated. However, this was not a division that diminished its infiniteness or created boundaries. Instead, the separation occurred horizontally. Because the waters were divided in this precise, infinite manner, both the expanse above and the expanse below retained their limitless nature. They were split, yet they both remained completely infinite.</p>
<p>Following this monumental division, the Only One chose to remain still, taking its eternal place upon the waters above. In this higher realm, the ultimate presence rested in perfect serenity, watching over the vast expanse.</p>
<h2>The Mirrored Universe</h2>
<p>Meanwhile, a magnificent transformation began to unfold within the waters that lay beneath. Guided by the grand design, the lower waters began to shift and take shape, forming a brand new universe similar to the one above.</p>
<h2>The Masterpiece and the Prize</h2>
<p>This mirrored universe below was not created without a specific, profound purpose. It was designed as an ultimate prize, a divine gift intended specifically for The Hand.</p>
<p>Because The Hand was the entity responsible for executing the will of the Only One, it was The Hand who actually built everything—every structure, every expanse, and every detail. Therefore, the universe itself became both his masterpiece and his ultimate reward. The very work he poured into creation was the prize he was meant to inherit and rule.</p>
<h2>The Unfinished Celebration</h2>
<p>To honor this monumental achievement, a grand ceremony was planned. It was to be a glorious inauguration across the cosmos to celebrate The Hand's flawless work and to officially bestow upon him the magnificent universe he had built.</p>
<p>The stage was set, the universe was complete, and everything resonated in a state of absolute, perfect harmony. Everything was fine...</p>
<p class="italic muted">Until something happened that changed everything.</p>
<div class="continued"><p>To be continued …</p></div>
""",
    },
    {
        "id": 1,
        "title": "The Separation of the Only One",
        "episode": "S1E1",
        "excerpt": (
            "Explore the origins of the universe through the deliberate separation of the Only One "
            "into three distinct entities..."
        ),
        "date_display": "15 March 2026",
        "image": "Olife1.comBlogposts1e1.png",
        "seo_title": "The Separation of the Only One: Science, Faith, and the Ultimate Source",
        "seo_description": (
            "Explore the origins of the universe through the deliberate separation of the Only One "
            "into three distinct entities: the receiver, the Hand, and the intelligence."
        ),
        "seo_keywords": (
            "The Only One, science and faith, origin of the universe, spiritual analysis, "
            "Genesis, Big Noise theory"
        ),
        "sort_order": 1,
        "content_html": """
<p>Once upon a time, there was the Only One: a single presence infinite in power, infinite in energy, and boundless in its existence. In this solitary state, it was completely perfect. It lacked nothing, needing neither space nor time, existing simply as the ultimate, flawless source of everything that would ever be.</p>
<h2>The Two Paths of Understanding: Science and Religion</h2>
<p>In a universe that is full of living beings, species have given this ultimate source many different names. When trying to understand it, they generally divide into two main groups: the scientists and the religious. Each group has its own unique way of describing this perfect existence, relying on entirely different foundations. Some view it through the strict lens of logic and the observation of the known, while others rely deeply on faith and a reverence for the unknown.</p>
<p>Regardless of which side they look from, there was a specific moment when a profound decision was made. This is the turning point that most religions refer to as the beginning. In the big book, for example, it is famously called Genesis. On the other hand, scientists have their own explanations for this exact same moment of creation, most notably referring to it as the Big Noise theory.</p>
<h2>The Great Separation</h2>
<p>But what really happened at that moment? This monumental event was not just an explosion or a simple act of creation, but a deliberate separation. It was the moment the Only One decided to divide itself into three distinct entities, often described as the physical, the essence, and the intelligence.</p>
<p>Operating in its infinite wisdom, the Only One chose to split itself into these different, specialized parts.</p>
<h3>The Triad of Existence: Matter, Worker, and Intelligence</h3>
<ul class="triad">
  <li><strong>The Receiver:</strong> First, there is the main part, often considered the matter or the receiver. It can be considered as the core where everything is taken in and processed.</li>
  <li><strong>The Hand:</strong> Second, there is the part called the worker, also known as the Hand. This is the active force, the entity that takes the processed information and actually executes the action.</li>
  <li><strong>The Intelligence:</strong> Finally, there is the intelligence. The intelligence acts as the mind and the voice, the entity that communicates and connects it all.</li>
</ul>
<p>Together, the receiver processes the reality, the Hand executes the will, and the intelligence communicates the grand design. Though they are now three, they work in perfect harmony.</p>
<div class="continued"><p>To be continued …</p></div>
""",
    },
]


class Command(BaseCommand):
    help = "Seed Olife blog posts and fragments from the React site content."

    def handle(self, *args, **options):
        for item in FRAGMENTS:
            Fragment.objects.update_or_create(
                pk=item["id"],
                defaults={
                    "title": item["title"],
                    "alt_text": item["alt_text"],
                    "image": item["image"],
                    "sort_order": item["sort_order"],
                    "is_published": True,
                },
            )
        for item in POSTS:
            BlogPost.objects.update_or_create(
                pk=item["id"],
                defaults={
                    "title": item["title"],
                    "episode": item["episode"],
                    "excerpt": item["excerpt"],
                    "date_display": item["date_display"],
                    "image": item["image"],
                    "seo_title": item["seo_title"],
                    "seo_description": item["seo_description"],
                    "seo_keywords": item["seo_keywords"],
                    "content_html": item["content_html"].strip(),
                    "sort_order": item["sort_order"],
                    "is_published": True,
                },
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(FRAGMENTS)} fragments and {len(POSTS)} blog posts."
            )
        )
