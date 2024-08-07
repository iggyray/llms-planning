class node_db:
    def __init__(self, init_state) -> None:
        self.db = {}
        self.node_index = 0
        self.add_root_node(init_state)
    
    def get_node_index_str(self):
        cur_node_index = str(self.node_index)
        self.node_index += 1
        return cur_node_index
    
    def add_root_node(self, init_state):
        cur_node_index = self.get_node_index_str()
        self.db[cur_node_index] = { "parent_id": None, "action": None, "state": init_state }
    
    def add_node(self, action, parent_id):
        if parent_id not in self.db:
            raise Exception('parent id does not exist')
        cur_node_index = self.get_node_index_str()
        self.db[cur_node_index] = { "parent_id": parent_id, "action": action }
        return cur_node_index
    
    def update_node_state(self, node_id, state):
        self.db[node_id]['state'] = state
    
    def get_action_from_id(self, node_id):
        return self.db[node_id]["action"]
    
    def get_state_from_id(self, node_id):
        return self.db[node_id]["state"]
    
    def get_parent_state_from_id(self, node_id):
        parent_id = self.db[node_id]["parent_id"]
        return self.db[parent_id]["state"]
    
    def get_plan(self, node_id, current_plan=None):
        cur_node = self.db[node_id]
        if current_plan is None:
            current_plan = []
        if cur_node["parent_id"] is None:
            plan_str = ''.join(current_plan)
            return plan_str
        
        current_plan.insert(0, cur_node['action'])
        next_node_id = cur_node['parent_id']
        return self.get_plan(next_node_id, current_plan)
    
    def get_cur_node_depth(self, node_id, total_depth=None):
        '''
        root_node_depth = 0, child_node_depth = 1, ... 
        '''
        cur_node = self.db[node_id]
        if total_depth is None:
            total_depth = 0
        if cur_node["parent_id"] is None:
            return total_depth
        
        total_depth += 1
        next_node_id = cur_node['parent_id']
        return self.get_cur_node_depth(next_node_id, total_depth)
    
    def get_all_nodes(self):
        return self.db
    
# if __name__=="__main__":
#     # arrange
#     test_node_db = node_db()
#     parent_node_id = test_node_db.add_node("hi")
#     child_node_id = test_node_db.add_node("ho", parent_node_id)
#     grandchild_node_id = test_node_db.add_node("ha", child_node_id)

#     # act
#     plan_list = test_node_db.get_plan(grandchild_node_id)

#     #
#     print(' '.join(plan_list))