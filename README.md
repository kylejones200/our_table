# Our Table - Recipe Collection

A Hugo-powered recipe website showcasing a collection of family recipes.

## 🚀 Deployment to GitHub Pages

This site is configured to automatically deploy to GitHub Pages using GitHub Actions.

### Setup Instructions

1. **Update Configuration**
   - Edit `hugo.toml` and replace `USERNAME` and `REPOSITORY_NAME` in the `baseURL` with your actual GitHub username and repository name:
   ```toml
   baseURL = 'https://yourusername.github.io/your-repo-name/'
   ```

2. **Enable GitHub Pages**
   - Go to your repository settings on GitHub
   - Navigate to "Pages" in the left sidebar
   - Under "Source", select "GitHub Actions"

3. **Push to GitHub**
   - The GitHub Actions workflow will automatically trigger on pushes to `main` or `master` branch
   - Your site will be built and deployed automatically

### Local Development

To run the site locally:

```bash
# Install Hugo (if not already installed)
# On macOS:
brew install hugo

# On other systems, see: https://gohugo.io/installation/

# Clone the repository
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name

# Start the development server
hugo server -D

# Open http://localhost:1313 in your browser
```

## 📁 Project Structure

```
├── .github/
│   └── workflows/
│       └── hugo.yml          # GitHub Actions workflow
├── content/
│   ├── _index.md            # Homepage content
│   └── recipes/             # Recipe markdown files
├── layouts/
│   ├── _default/
│   │   └── baseof.html      # Base template
│   ├── recipes/
│   │   ├── list.html        # Recipe listing page
│   │   └── single.html      # Individual recipe page
│   ├── shortcodes/          # Custom shortcodes
│   └── index.html           # Homepage template
├── static/                  # Static assets (images, etc.)
└── hugo.toml               # Hugo configuration
```

## ✍️ Adding New Recipes

Create a new markdown file in `content/recipes/` with the following front matter:

```yaml
---
title: "Recipe Name"
date: 2025-08-18
type: "recipe"
description: "Brief description of the recipe"
yield: "Serves 4"
prep_time: "15m"
cook_time: "30m"
total_time: "45m"
cuisines: ["Italian"]
courses: ["Main Course"]
diets: ["Vegetarian"]
tags: ["pasta", "quick", "family-friendly"]
equipment: ["Large pot", "Colander"]
image: "images/recipe-name/hero.jpg"
nutrition:
  calories: 350
  protein_g: 12
  carbs_g: 45
  fat_g: 14
---

## Ingredients

- 1 lb pasta
- 2 cups tomato sauce
- 1 cup cheese

## Instructions

1. Boil water in a large pot
2. Add pasta and cook according to package directions
3. Drain and serve with sauce and cheese

## Notes

Any additional notes or tips for the recipe.
```

## 🎨 Customization

- **Styling**: Modify the CSS in `layouts/_default/baseof.html`
- **Layout**: Update templates in the `layouts/` directory
- **Configuration**: Edit `hugo.toml` for site-wide settings

## 📝 Features

- ✅ Responsive design
- ✅ Recipe metadata (prep time, servings, etc.)
- ✅ Nutrition information support
- ✅ Tag and category system
- ✅ Image support
- ✅ SEO-friendly URLs
- ✅ Automatic GitHub Pages deployment

## 🔧 Troubleshooting

**Build fails on GitHub Actions:**
- Check that all markdown files have valid front matter
- Ensure image paths are correct
- Verify `hugo.toml` syntax

**Images not loading:**
- Place images in the `static/` directory
- Reference them in markdown as `images/folder/image.jpg`
- The `static/` prefix is automatically handled by Hugo

**Local development issues:**
- Make sure Hugo is installed and up to date
- Run `hugo server -D` to include draft content
- Check for syntax errors in templates

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
