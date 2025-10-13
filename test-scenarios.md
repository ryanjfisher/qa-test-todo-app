# Sample Test Scenarios for QA Platform

## Test 1: Add a new todo
1. Navigate to the application
2. Enter "Buy groceries" into the todo input field
3. Click the "Add Todo" button
4. Verify the todo appears in the list

## Test 2: Complete a todo
1. Add a new todo "Finish project"
2. Click the checkbox next to the todo
3. Verify the todo is marked as completed
4. Check that completed count increases

## Test 3: Delete a todo
1. Add a new todo "Temporary task"
2. Click the delete button for the todo
3. Verify the todo is removed from the list
4. Check that total count decreases

## Test 4: Multiple todos workflow
1. Add "First task"
2. Add "Second task"
3. Add "Third task"
4. Complete "Second task"
5. Delete "First task"
6. Verify only "Third task" (active) and "Second task" (completed) remain
7. Check statistics: Total=2, Active=1, Completed=1

## Test 5: Edge cases
1. Try to add an empty todo (should not add)
2. Add a todo with special characters "<script>alert('test')</script>"
3. Verify HTML is properly escaped
4. Add a very long todo text
5. Verify UI handles it gracefully