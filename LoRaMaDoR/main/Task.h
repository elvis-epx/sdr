#ifndef __TASK_H
#define __TASK_H

// inherited by classes that will supply callback methods for tasks

#include "Vector.h"
#include "Pointer.h"
#include "Dict.h"

class Task;

class TaskCallable {
public:
	virtual ~TaskCallable() {};
	virtual unsigned long int task_callback(int, unsigned long int, Task*) = 0;
};

class TaskManager;

// callback_target must outlive the Task.

class Task {
public:
	Task(int id, const char *name, unsigned long int offset, TaskCallable* callback_target);
	virtual ~Task();
	unsigned long int next_run() const;
	const char *get_name() const;

protected:
	virtual bool run(unsigned long int now);

private:
	friend class TaskManager;
	void set_timebase(unsigned long int timebase);
	bool should_run(unsigned long int now) const;
	bool cancelled() const;

	int id;
	const char *name;
	unsigned long int offset;
	unsigned long int timebase;
	TaskCallable *callback_target;

	// Tasks must be manipulated through (smart) pointers,
	// the pointer is the ID, no copies allowed
	Task() = delete;
	Task(const Task&) = delete;
	Task(const Task&&) = delete;
	Task& operator=(const Task&) = delete;
	Task& operator=(Task&&) = delete;
};

class TaskManager {
public:
	TaskManager();
	~TaskManager();
	void run(unsigned long int);
	void schedule(Ptr<Task> task);
	void cancel(const Task* task);
	// for testing purposes
	Ptr<Task> next_task() const;
private:
	Vector< Ptr<Task> > tasks;

	TaskManager(const TaskManager&) = delete;
	TaskManager(const TaskManager&&) = delete;
	TaskManager& operator=(const TaskManager&) = delete;
	TaskManager& operator=(TaskManager&&) = delete;
};

#endif
