// Todo App - QA Test Application
class TodoApp {
  constructor() {
    this.todos = this.loadTodos();
    this.init();
  }

  init() {
    this.todoInput = document.getElementById('todo-input');
    this.addBtn = document.getElementById('add-btn');
    this.todoList = document.getElementById('todo-list');
    this.emptyState = document.getElementById('empty-state');
    
    this.addBtn.addEventListener('click', () => this.addTodo());
    this.todoInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.addTodo();
      }
    });
    
    this.render();
  }

  loadTodos() {
    const stored = localStorage.getItem('todos');
    return stored ? JSON.parse(stored) : [];
  }

  saveTodos() {
    localStorage.setItem('todos', JSON.stringify(this.todos));
  }

  addTodo() {
    const text = this.todoInput.value.trim();
    if (!text) return;
    
    const todo = {
      id: Date.now().toString(),
      text: text,
      completed: false,
      createdAt: new Date().toISOString()
    };
    
    this.todos.unshift(todo);
    this.saveTodos();
    this.todoInput.value = '';
    this.render();
  }

  toggleTodo(id) {
    const todo = this.todos.find(t => t.id === id);
    if (todo) {
      todo.completed = !todo.completed;
      this.saveTodos();
      this.render();
    }
  }

  deleteTodo(id) {
    this.todos = this.todos.filter(t => t.id !== id);
    this.saveTodos();
    this.render();
  }

  render() {
    // Clear the list
    this.todoList.innerHTML = '';
    
    // Show/hide empty state
    if (this.todos.length === 0) {
      this.emptyState.style.display = 'block';
      this.todoList.style.display = 'none';
    } else {
      this.emptyState.style.display = 'none';
      this.todoList.style.display = 'block';
      
      // Render todos
      this.todos.forEach(todo => {
        const li = document.createElement('li');
        li.className = 'todo-item' + (todo.completed ? ' completed' : '');
        li.setAttribute('data-testid', `todo-item-${todo.id}`);
        
        li.innerHTML = `
          <input 
            type="checkbox" 
            class="todo-checkbox" 
            ${todo.completed ? 'checked' : ''}
            data-testid="checkbox-${todo.id}"
          />
          <span class="todo-text" data-testid="text-${todo.id}">${this.escapeHtml(todo.text)}</span>
          <button class="delete-btn" data-testid="button-delete-${todo.id}">Delete</button>
        `;
        
        // Add event listeners
        const checkbox = li.querySelector('.todo-checkbox');
        const deleteBtn = li.querySelector('.delete-btn');
        
        checkbox.addEventListener('change', () => this.toggleTodo(todo.id));
        deleteBtn.addEventListener('click', () => this.deleteTodo(todo.id));
        
        this.todoList.appendChild(li);
      });
    }
    
    // Update stats
    this.updateStats();
  }

  updateStats() {
    const total = this.todos.length;
    const completed = this.todos.filter(t => t.completed).length;
    const active = total - completed;
    
    document.getElementById('total-count').textContent = total;
    document.getElementById('active-count').textContent = active;
    document.getElementById('completed-count').textContent = completed;
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new TodoApp();
});