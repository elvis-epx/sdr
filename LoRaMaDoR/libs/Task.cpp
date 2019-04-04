#include "Task.h"
#include "FakeArduino.h"

Task::Task(int id, unsigned long int offset, TaskCallable* callback_target)
{
	this->id = id;
	this->offset = offset;
	this->timebase = 0;
	this->callback_target = callback_target;
}

Task::~Task()
{
	this->callback_target = 0;
	this->timebase = 0;
}

void Task::set_timebase(unsigned long int now)
{
	this->timebase = now;
}

bool Task::should_run(unsigned long int now) const
{
	return this->timebase > 0 && 
		(this->timebase + this->offset) <= now;
}

bool Task::cancelled() const
{
	return this->timebase <= 0;
}

bool Task::run(unsigned long int now)
{
	// callback returns new timeout (which could be random)
	this->offset = callback_target->task_callback(id, now, this);
	// task cancelled by default, rescheduled by task mgr
	this->timebase = 0;
	return this->offset > 0;
}

TaskManager::TaskManager() {}

TaskManager::~TaskManager() {}

void TaskManager::schedule(Task* task)
{
	Ptr<Task> etask = task;
	tasks.push_back(etask);
	etask->set_timebase(arduino_millis());
}

void TaskManager::cancel(const Task *task)
{
	for (unsigned int i = 0 ; i < tasks.size(); ++i) {
		if (tasks[i].id() == task) {
			tasks.remov(i);
			break;
		}
	}
}

void TaskManager::run(unsigned long int now)
{
	bool dirty = false;

	for (unsigned int i = 0 ; i < tasks.size(); ++i) {
		Ptr<Task> t = tasks[i];
		if (t->should_run(now)) {
			bool stay = t->run(now);
			if (stay) {
				// reschedule
				t->set_timebase(arduino_millis());
			} else {
				// task list must be pruned
				dirty = true;
			}
		}
	}

	while (dirty) {
		dirty = false;
		for (unsigned int i = 0 ; i < tasks.size(); ++i) {
			Ptr<Task> t = tasks[i];
			if (t->cancelled()) {
				tasks.remov(i);
				dirty = true;
				break;
			}
		}
	}
}
