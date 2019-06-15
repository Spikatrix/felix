"""This is a cog for a discord.py bot.
It hides the help command and adds these commands:

    helpall     show all commands (including all hidden ones)

    The commands will output to the current channel or to a dm channel
    according to the pm_help kwarg of the bot.

Only users belonging to a role that is specified under the module's name
in the permissions.json file can use the commands.
"""

import itertools
from discord import Embed
from discord.ext import commands
from discord.ext.commands import HelpCommand, Command, Group, DefaultHelpCommand


class myHelpCommand(HelpCommand):
    def __init__(self, **options):
        super().__init__(**options)
        self.paginator = None

    async def send_pages(self):
        destination = self.get_destination()
        embed = Embed(
        )
        embed.set_author(
            name=self.context.bot.description,
            icon_url=self.context.bot.user.avatar_url
        )
        for category, entries in self.paginator:
            embed.add_field(
                name=category,
                value=entries,
                inline=False
            )
        embed.set_footer(
            text='Use felix help <command/category> for more information.'
        )
        await destination.send(embed=embed)

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        def get_category(command):
            cog = command.cog
            return cog.qualified_name + ':' if cog is not None else 'Default:'

        filtered = await self.filter_commands(
            bot.commands,
            sort=True,
            key=get_category
        )
        to_iterate = itertools.groupby(filtered, key=get_category)
        for cog_name, command_grouper in to_iterate:
            cmds = sorted(command_grouper, key=lambda c: c.name)
            category = f'► {cog_name}'
            if len(cmds) == 1 and cmds[0].name.lower() in category.lower():
                entries = f'{cmds[0].name} → {cmds[0].short_doc}'
            else:
                entries = ' | '.join([command.name for command in cmds])
            self.paginator.append((category, entries))
        await self.send_pages()

    async def send_cog_help(self, cog):
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        if not filtered:
            await self.context.send(
                'No public commands in this cog. Try again with felix helpall.'
            )
            return
        category = f'▼ {cog.qualified_name}'
        entries = '\n'.join(
            f'**{command.name}** → {command.short_doc or command.description}'
            for command in filtered
        )
        print(entries)
        self.paginator.append((category, entries))
        await self.send_pages()

    async def send_group_help(self, group):
        filtered = await self.filter_commands(group.commands, sort=True)
        category = f'**{group.name}** - {group.description or group.short_doc}'
        entries = '\n'.join(
            f'**{command.name}** → {command.short_doc}' for command in filtered
        )
        self.paginator.append((category, entries))
        await self.send_pages()

    async def send_command_help(self, command):
        signature = self.get_command_signature(command)
        helptext = command.help or command.description or 'No help Text'
        self.paginator.append(
            (signature,  helptext)
        )
        await self.send_pages()

    async def prepare_help_command(self, ctx, command=None):
        self.paginator = []
        await super().prepare_help_command(ctx, command)


class Help(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.client.help_command = myHelpCommand()
        self.client.get_command('help').hidden = True

    async def cog_check(self, ctx):
        return self.client.user_has_permission(ctx.author, 'helpall')

    def cog_unload(self):
        self.client.get_command('help').hidden = False
        self.client.help_command = DefaultHelpCommand()

    @commands.command(
        name='helpall',
        hidden=True
    )
    @commands.guild_only()
    async def helpall(self, ctx, *, text=None):
        """Print bot help including all hidden commands"""
        self.client.help_command = myHelpCommand(show_hidden=True)
        if text:
            await ctx.send_help(text)
        else:
            await ctx.send_help()
        self.client.help_command = myHelpCommand()


def setup(client):
    client.add_cog(Help(client))
