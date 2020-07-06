---
layout: default
title: Joi's GitHub Jekyll Page
---

* [Recipes](food/recipe_list/)
* [Coffee Basics](food/coffee-basics)
* [Common Ingredients by Volume and Mass](food/ingredients-volume-mass)
* [Volume, Weight and Temperature Conversions](food/volume-weight-temp)

{% for recipe in site.recipes %}
    <h2><a href="{{ recipe.url }}">{{ recipe.url }}</a></h2>
{% endfor %}

<ul>
  {% for post in site.posts %}
    <li><a href="{{ post.url }}">{{ post.title }}</a>
    </li>
  {% endfor %}
</ul>