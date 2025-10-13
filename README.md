# QA Test Todo Application

A simple todo application designed for testing the QA Automation Platform.

## Features

- ✅ Add new todos
- ✅ Mark todos as complete/incomplete
- ✅ Delete todos
- ✅ Persistent storage using localStorage
- ✅ Statistics tracking (total, active, completed)
- ✅ Responsive design
- ✅ Data-testid attributes for automated testing

## Testing Elements

This application includes comprehensive data-testid attributes for automated testing:

### Input Fields
- `data-testid="input-todo"` - Main todo input field

### Buttons
- `data-testid="button-add-todo"` - Add todo button
- `data-testid="button-delete-{id}"` - Delete buttons for each todo

### Lists and Items
- `data-testid="list-todos"` - Todo list container
- `data-testid="todo-item-{id}"` - Individual todo items
- `data-testid="checkbox-{id}"` - Todo completion checkboxes
- `data-testid="text-{id}"` - Todo text content

### Statistics
- `data-testid="stat-total"` - Total todos count
- `data-testid="stat-active"` - Active todos count
- `data-testid="stat-completed"` - Completed todos count

## Test Scenarios

Perfect for testing:
1. **Form interactions** - Adding todos via button click or Enter key
2. **State management** - Checking/unchecking todos
3. **CRUD operations** - Create, read, update, delete todos
4. **Data persistence** - LocalStorage functionality
5. **UI updates** - Dynamic rendering and statistics
6. **Edge cases** - Empty states, long text, special characters

## How to Use

1. Open index.html in a browser
2. Start adding todos
3. Test various interactions
4. Use the QA Automation Platform to run automated tests

## Technologies

- Pure HTML5
- CSS3 with modern styling
- Vanilla JavaScript (ES6+)
- LocalStorage API

## Live Demo

Visit the GitHub Pages deployment (if enabled) or clone and open index.html locally.

---

Built specifically for testing with the QA Automation Platform 🚀