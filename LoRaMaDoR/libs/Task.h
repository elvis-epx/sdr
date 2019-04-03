#ifndef __TASK_H
#define __TASK_H

// inherited by classes that will supply callback methods for tasks

class TaskCallable {
	virtual ~TaskCallable() {}
};

class TaskManager;

// TaskManager and cb_target must outlive the Task.

class Task {
public:
	Task(TaskManager *mgr,
		long int offset,
		TaskCallable* cb_target,
		long int (TaskCallable::*callback)(const Task*));
	~Task();

private:
	friend class TaskManager;
	bool set_timebase(long int timebase);
	bool should_run(long int now) const;
	bool run();

	TaskManager *mgr;
	long int offset;
	long int timebase;
	TaskCallable *cb_target;
	long int (TaskCallable::*callback)(const Task*);

	// Tasks must be manipulated through (smart) pointers,
	// the pointer is the ID, no copies whatsoever
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
	bool run(long int now);
	void schedule(Task* task);
	void cancel(const Task* task);
private:
	Vector< Ptr<Task> > tasks;

	// TaskManager should not be copied around
	TaskManager() = delete;
	TaskManager(const TaskManager&) = delete;
	TaskManager(const TaskManager&&) = delete;
	TaskManager& operator=(const TaskManager&) = delete;
	TaskManager& operator=(TaskManager&&) = delete;

};

#endif
