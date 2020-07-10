---
layout: default
title: Joi's GitHub Jekyll Page
---

During the COVID-19 lockdown, I have started cooking a lot more - almost every dinner. While planning my cooking, I decided to organize my recipes. I noticed that the app that I was using, [Paprika](https://www.paprikaapp.com/), could export to html so I set up [GitHub Pages](https://pages.github.com/) and [Jekyll](https://jekyllrb.com/) and had GitHub serve the site. I thought that this would be a good GitHub project to become more familiar with GitHub as well.

Boris Anthony who has worked with me on my website since the beginning is now helping me with this.

As I've continued to cook and read books like [Salt Fat Acid Heat by Samin Nosrat](https://www.saltfatacidheat.com/) and [The Food Lab by J. Kenji López-Alt](http://www.kenjilopezalt.com/), I realized that it wasn't so much about recipes and that the underlying theory and the practical experience were super important. I decided to use the blog posts feature in Jekyll and begin documenting my cooking experiments. I have decided to use the date that the cooking occurred, not when I wrote the post to  keep the posts and my calendar more synced.

I've also started to create some basic guides as references for my cooking.

* [Recipes](food/recipe_list/)
* [Coffee Basics](food/coffee-basics)
* [Common Ingredients by Volume and Mass](food/ingredients-volume-mass)
* [Volume, Weight and Temperature Conversions](food/volume-weight-temp)


# For Post in Posts

<ul>
  {% for post in site.posts %}
    <li><a href="{{ post.url }}">{{post.date | date: '%B %d, %Y' }} - {{ post.title }}</a></li>
  {% endfor %}
</ul>

---

# For Recipe in Site.Recipes

<ul class="recipes">
  {% for recipe in site.recipes_md %}
  	{% assign json_data = site.data.recipes[recipe.filename] %}
    <li>
    	<a href="{{ recipe.url }}">
    	{% if json_data.photo_data %}
    		<img style='width:100px;heigh:100px;' src='data:imge/jpeg;base64,{{json_data.photo_data}}' />
    	{% else %}
    		<img style='width:100px;heigh:100px;' src='/images/200x200.gif' />
    	{% endif %}
    	{{ recipe.title }}
    	</a>
    </li>
  {% endfor %}
</ul>

---