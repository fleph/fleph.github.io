---
permalink: /blog/
title: "Blog"
excerpt: "Notes, essays, and updates."
author_profile: true
---

# Blog

{% if site.posts.size > 0 %}
<div class="archive">
{% for post in site.posts %}
  <article class="archive__item">
    <h2 class="archive__item-title">
      <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
    </h2>
    <p class="page__meta">
      <time datetime="{{ post.date | date_to_xmlschema }}">{{ post.date | date: "%Y.%m.%d" }}</time>
      {% if post.categories.size > 0 %} - {{ post.categories | join: ", " }}{% endif %}
    </p>
    {% if post.excerpt %}
      <p class="archive__item-excerpt">{{ post.excerpt | markdownify | strip_html | truncate: 180 }}</p>
    {% endif %}
  </article>
{% endfor %}
</div>
{% else %}
No posts yet.
{% endif %}
