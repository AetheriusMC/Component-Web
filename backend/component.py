"""
Aetherius Component: Web - 组件入口点
===================================

符合Aetherius核心规范的组件入口
"""

# 导入组件信息和实例创建函数
from component_info import component_info
from web_component import create_component

# 这是Aetherius核心加载组件时查找的标准入口
__component_info__ = component_info
__create_component__ = create_component

# 版本信息
__version__ = "0.1.0"
__author__ = "Aetherius Team"